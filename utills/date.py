from datetime import datetime

def format_job_posted_date(date):
        """
        Format the job creation date into a readable format
        
        Args:
            date: Datetime or string representing job creation date
            
        Returns:
            str: Formatted date string
        """
        if not date:
            return "Recently"
        
        try:
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            
            # Calculate days ago
            days_ago = (datetime.now(timezone.utc) - date).days
            
            if days_ago == 0:
                return "Today"
            elif days_ago == 1:
                return "Yesterday"
            else:
                return f"{days_ago} days ago"
        except Exception:
            return "Recently"