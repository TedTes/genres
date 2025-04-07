import asyncio
import logging
from services.scraper.data_aggregator import DataAggregator
from db import db
from app import app
from parser_configs import configs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_aggregation():
    """Run the DataAggregator and store results in Supabase."""
    try:
        logger.info("Starting aggregation run")
        aggregator = DataAggregator(configs)
        jobs = await aggregator.aggregate()
        logger.info(f"Aggregation complete: {len(jobs)} jobs collected and stored")
    except Exception as e:
        logger.error(f"Error during aggregation: {str(e)}")
        db.session.rollback()
    finally:
        db.session.close()

def main():
    """Run the aggregation once within Flask app context."""
    with app.app_context():
        asyncio.run(run_aggregation())

if __name__ == "__main__":
    main()