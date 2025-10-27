initial_setup_macos:
	@echo "Setting up the development environment ..."
	python3 -m venv venv
	source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Development environment setup complete."

initial_setup_windows:
	@echo "Setting up the development environment ..."
	python -m venv venv
	.\venv\Scripts\activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Development environment setup complete."

run_dashboard:
	@echo "Starting the Streamlit dashboard ..."
	streamlit run dashboard/dashboard.py
	@echo "Dashboard is running."

run_scrapping:
	@echo "Executing the web scraping script ..."
	python scrapping/scrape_books.py
	@echo "Web scraping completed."

run_api:
	@echo "Starting the FastAPI server ..."
	uvicorn api.main:app --reload
	@echo "API server is running."
