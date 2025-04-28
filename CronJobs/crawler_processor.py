import os
import time
import json
import requests
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from UtilityFunctions.openai_gpt import openai_route
from SystemFiles.prompts import CONTACT_EXTRACTOR_PROMPT
from datetime import datetime

class ContactCrawler:
    def __init__(self, start_url, user_id, crawler_manager, session_id, depth, max_pages):
        """
        :param start_url: URL to start crawling from.
        :param user_id: User identifier for MongoDB.
        :param crawler_manager: Existing instance of CrawlerManager from DatabaseManager.
        :param session_id: Existing session ID to use for this crawl.
        :param depth: Recursion depth for crawling.
        :param max_pages: Maximum number of pages to crawl.
        """
        self.start_url = start_url
        self.user_id = user_id
        self.depth = depth
        self.max_pages = max_pages
        self.visited = set()
        self.all_contacts = []
        self.log_counter = 0
        self.crawler_manager = crawler_manager
        self.session_id = session_id
        self.log_messages = {}
        self._crawler_thread = None

    def log_update(self, messages):
        """Update logs using crawler_manager."""
        self.log_counter += 1
        update = " | ".join(messages)
        self.log_messages[str(self.log_counter)] = update
        self.crawler_manager.add_crawler_log(
            self.user_id,
            self.session_id,
            str(self.log_counter),
            update
        )

    def _update_progress(self):
        """Update progress using crawler_manager."""
        progress_data = {
            "pages_visited": len(self.visited),
            "total_contacts": len(self.all_contacts),
            "unique_contacts": len(set(contact.get("email", "") for contact in self.all_contacts if contact.get("email")))
        }
        self.crawler_manager.update_crawler_progress(
            self.user_id,
            self.session_id,
            progress_data
        )

    def _update_contacts(self, new_contacts):
        """Update contacts using crawler_manager."""
        self.crawler_manager.update_crawler_contacts(
            self.user_id,
            self.session_id,
            new_contacts
        )

    def get_links(self, soup, base_url):
        return {
            urljoin(base_url, a['href'])
            for a in soup.find_all("a", href=True)
            if urljoin(base_url, a['href']).startswith("http")
            and urlparse(urljoin(base_url, a['href'])).netloc == urlparse(base_url).netloc
        }

    def extract_contact_blocks(self, soup):
        # Grab up to 3 elements potentially containing contact details.
        return [
            tag.get_text(" ", strip=True)
            for tag in soup.find_all(['p', 'div', 'li', 'section'])
            if '@' in tag.text or 'contact' in tag.text.lower() or 'director' in tag.text.lower()
        ][:3]

    def crawl(self, url, depth):
        # Stop if we have reached the maximum page limit.
        if len(self.visited) >= self.max_pages:
            self.log_update([f"MaxPagesReached: {self.max_pages} pages reached. Stopping crawl."])
            return
        
        if url in self.visited or depth < 0:
            return
        
        self.visited.add(url)
        # Build log message (depth info omitted).
        log_items = [
            f"URL: {url}",
            f"PagesVisited: {len(self.visited)}",
            f"CumulativeContacts: {len(self.all_contacts)}"
        ]
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla"})
            soup = BeautifulSoup(response.text, "html.parser")
            blocks = self.extract_contact_blocks(soup)
            new_contacts = openai_route(CONTACT_EXTRACTOR_PROMPT.format(text=str(blocks), source_url=url))
            new_contacts = new_contacts.replace('```json', '').replace('```', '')
            try:
                parsed_contacts = json.loads(new_contacts)
                if isinstance(parsed_contacts, list):
                    self.all_contacts.extend(parsed_contacts)
                    self._update_contacts(self.all_contacts)
            except json.JSONDecodeError as e:
                self.log_update([f"JSON Parse Error: {str(e)}"])
                return
            time.sleep(0.5)
            # Update cumulative contact count.
            log_items[-1] = f"CumulativeContacts: {len(self.all_contacts)}"
        except Exception as e:
            log_items.append(f"Error: {str(e)}")
            self.log_update(log_items)
            return

        self.log_update(log_items)
        self._update_progress()

        # Recursively crawl linked pages.
        for link in self.get_links(soup, url):
            if len(self.visited) >= self.max_pages:
                self.log_update([f"MaxPagesReached: {self.max_pages} pages reached. Stopping further crawl."])
                break
            self.crawl(link, depth - 1)

    def _run_crawler(self):
        """Internal method to run the crawler."""
        try:
            # Update status to running
            self.crawler_manager.update_crawler_session(
                self.user_id,
                self.session_id,
                {"status": "running"}
            )
            
            self.log_update([f"StartingCrawler from: {self.start_url} | InitialDepth: {self.depth} | MaxPages: {self.max_pages}"])
            
            self.crawl(self.start_url, self.depth)
            
            # Deduplicate contacts by email if available
            unique_contacts = []
            seen_emails = set()
            
            for contact in self.all_contacts:
                if isinstance(contact, dict) and "email" in contact:
                    email = contact["email"].lower().strip()
                    if email and email not in seen_emails:
                        seen_emails.add(email)
                        unique_contacts.append(contact)
            
            final_log = [
                "FinalResults",
                f"PagesVisited: {len(self.visited)}",
                f"TotalContacts: {len(self.all_contacts)}",
                f"UniqueContacts: {len(unique_contacts)}"
            ]
            self.log_update(final_log)
            
            # Update final state while preserving all fields
            self.crawler_manager.update_crawler_session(
                self.user_id,
                self.session_id,
                {
                    "status": "completed",
                    "end_time": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "progress": {
                        "pages_visited": len(self.visited),
                        "total_contacts": len(self.all_contacts),
                        "unique_contacts": len(unique_contacts)
                    },
                    "contacts": self.all_contacts,
                    "logs": self.log_messages
                }
            )
            
        except Exception as e:
            self.log_update([f"Error: {str(e)}"])
            self.crawler_manager.update_crawler_session(
                self.user_id,
                self.session_id,
                {"status": "failed"}
            )
            raise

    def run(self):
        """Start the crawler in a separate thread."""
        self._crawler_thread = threading.Thread(target=self._run_crawler)
        self._crawler_thread.daemon = True  # Thread will exit when main program exits
        self._crawler_thread.start()
        return self.session_id