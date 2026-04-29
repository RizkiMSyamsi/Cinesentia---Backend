"""
Celery task for the full analysis pipeline:
  1. Fetch video metadata
  2. Scrape English comments
  3. Preprocess each comment
  4. Run ML model + VADER inference
  5. Bulk insert comments into DB
  6. Embed comments into ChromaDB
  7. Calculate aggregated statistics
"""

import logging
from collections import Counter
from datetime import datetime, timezone

from celery import shared_task

from app.extensions import db
from app.models.analysis import Analysis
from app.models.comment import Comment

logger = logging.getLogger(__name__)


def _update_status(analysis, status, progress, error=None):
    """Helper to update analysis status and commit."""
    analysis.status = status
    analysis.progress = progress
    if error:
        analysis.error_message = error
    db.session.commit()


@shared_task(bind=True, max_retries=2)
def run_analysis_pipeline(self, analysis_id, max_comments=10000):
    """
    Full analysis pipeline. Runs as a Celery task.
    
    Must be called within Flask app context (handled by ContextTask in celery_worker.py).
    """
    from app.services.youtube_service import YouTubeService
    from app.services.preprocessing_service import preprocess_text
    from app.services.ml_service import MLService
    from app.services.chroma_service import ChromaService

    analysis = Analysis.query.get(analysis_id)
    if not analysis:
        logger.error(f"Analysis {analysis_id} not found")
        return

    try:
        analysis.started_at = datetime.now(timezone.utc)
        _update_status(analysis, "fetching", 5)

        # Step 1: Fetch video metadata
        logger.info(f"[{analysis_id}] Fetching video metadata...")
        metadata = YouTubeService.get_video_metadata(analysis.video_id)
        analysis.video_title = metadata["video_title"]
        analysis.channel_name = metadata["channel_name"]
        analysis.thumbnail_url = metadata["thumbnail_url"]
        analysis.view_count = metadata["view_count"]
        _update_status(analysis, "fetching", 10)

        # Step 2: Scrape comments
        logger.info(f"[{analysis_id}] Scraping comments (max {max_comments})...")

        def on_scrape_progress(fetched, total):
            pct = 10 + int((fetched / max(total, 1)) * 30)
            analysis.progress = min(pct, 40)
            db.session.commit()

        raw_comments = YouTubeService.scrape_comments(
            analysis.video_id,
            max_comments=max_comments,
            on_progress=on_scrape_progress,
        )
        logger.info(f"[{analysis_id}] Scraped {len(raw_comments)} English comments")
        _update_status(analysis, "analyzing", 40)

        # Step 3 & 4: Preprocess + ML inference
        logger.info(f"[{analysis_id}] Running preprocessing & inference...")
        ml = MLService.get_instance()
        comment_records = []
        chroma_data = []

        for i, original_text in enumerate(raw_comments):
            # Preprocess
            preprocessed = preprocess_text(original_text)

            # ML + VADER prediction
            prediction = ml.predict(original_text, preprocessed)

            comment = Comment(
                analysis_id=analysis_id,
                original_text=original_text,
                preprocessed_text=preprocessed,
                model_sentiment=prediction["model_sentiment"],
                model_confidence=prediction["model_confidence"],
                vader_original_score=prediction["vader_original_score"],
                vader_original_label=prediction["vader_original_label"],
                vader_processed_score=prediction["vader_processed_score"],
                vader_processed_label=prediction["vader_processed_label"],
            )
            comment_records.append(comment)

            chroma_data.append({
                "id": comment.id,
                "preprocessed_text": preprocessed,
                "original_text": original_text,
                "model_sentiment": prediction["model_sentiment"],
                "model_confidence": prediction["model_confidence"],
            })

            # Update progress periodically
            if (i + 1) % 200 == 0:
                pct = 40 + int(((i + 1) / len(raw_comments)) * 40)
                analysis.progress = min(pct, 80)
                db.session.commit()

        # Step 5: Bulk insert comments
        logger.info(f"[{analysis_id}] Inserting {len(comment_records)} comments into DB...")
        db.session.bulk_save_objects(comment_records)
        _update_status(analysis, "embedding", 80)

        # Step 6: Embed into ChromaDB
        logger.info(f"[{analysis_id}] Embedding comments into ChromaDB...")
        chroma = ChromaService.get_instance()
        chroma.embed_comments(analysis_id, chroma_data)
        _update_status(analysis, "embedding", 95)

        # Step 7: Calculate aggregated statistics
        total = len(comment_records)
        sentiments = [c.model_sentiment for c in comment_records]
        counter = Counter(sentiments)

        analysis.total_comments = total
        analysis.positive_count = counter.get("positive", 0)
        analysis.negative_count = counter.get("negative", 0)
        analysis.neutral_count = counter.get("neutral", 0)
        analysis.positive_pct = round(
            (analysis.positive_count / max(total, 1)) * 100, 2
        )
        analysis.negative_pct = round(
            (analysis.negative_count / max(total, 1)) * 100, 2
        )
        analysis.neutral_pct = round(
            (analysis.neutral_count / max(total, 1)) * 100, 2
        )

        # VADER summary
        vader_counter = Counter(c.vader_processed_label for c in comment_records)
        analysis.vader_summary = {
            "positive": round((vader_counter.get("positive", 0) / max(total, 1)) * 100, 2),
            "negative": round((vader_counter.get("negative", 0) / max(total, 1)) * 100, 2),
            "neutral": round((vader_counter.get("neutral", 0) / max(total, 1)) * 100, 2),
        }
        analysis.model_summary = {
            "positive": analysis.positive_pct,
            "negative": analysis.negative_pct,
            "neutral": analysis.neutral_pct,
        }

        # Top keyword (simple: most common word in preprocessed text)
        all_words = " ".join(c.preprocessed_text or "" for c in comment_records).split()
        if all_words:
            word_counter = Counter(w for w in all_words if len(w) > 3)
            analysis.top_keyword = word_counter.most_common(1)[0][0] if word_counter else None

        analysis.completed_at = datetime.now(timezone.utc)
        _update_status(analysis, "completed", 100)
        logger.info(f"[{analysis_id}] Analysis completed successfully!")

    except Exception as e:
        logger.error(f"[{analysis_id}] Pipeline failed: {e}", exc_info=True)
        _update_status(analysis, "failed", analysis.progress, error=str(e))
