"""
PostgreSQL Database Optimizations
Custom migration for PostgreSQL-specific features
"""
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0006_aianalysissession_ai_recommendations'),
    ]

    operations = [
        # Add GIN indexes for JSON fields (better for AI analysis)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS reviews_review_ai_positive_keywords_gin ON reviews_review USING GIN (ai_positive_keywords);",
            reverse_sql="DROP INDEX IF EXISTS reviews_review_ai_positive_keywords_gin;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS reviews_review_ai_negative_keywords_gin ON reviews_review USING GIN (ai_negative_keywords);",
            reverse_sql="DROP INDEX IF EXISTS reviews_review_ai_negative_keywords_gin;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS reviews_review_ai_topics_analysis_gin ON reviews_review USING GIN (ai_topics_analysis);",
            reverse_sql="DROP INDEX IF EXISTS reviews_review_ai_topics_analysis_gin;"
        ),
        
        # Add full-text search index for review text
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS reviews_review_text_fts ON reviews_review USING GIN (to_tsvector('english', text));",
            reverse_sql="DROP INDEX IF EXISTS reviews_review_text_fts;"
        ),
        
        # Add composite indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS reviews_review_hotel_sentiment_score ON reviews_review (hotel_id, sentiment, ai_score);",
            reverse_sql="DROP INDEX IF EXISTS reviews_review_hotel_sentiment_score;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS reviews_review_date_sentiment ON reviews_review (date_posted, sentiment);",
            reverse_sql="DROP INDEX IF EXISTS reviews_review_date_sentiment;"
        ),
    ]