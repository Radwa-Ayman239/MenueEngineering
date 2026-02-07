
# Menu Engineering AI Platform

**Deloitte Hackathon Submission**

## Project Description

This project allows restaurant managers to analyze their menu performance using data-driven insights. It combines traditional Menu Engineering (BCG Matrix) with AI to help identify profitable items, underperformers, and opportunities for optimization.

The system analyzes sales data to classify items into four categories:
*   **Stars**: High profit, high popularity.
*   **Plowhorses**: Low profit, high popularity.
*   **Puzzles**: High profit, low popularity.
*   **Dogs**: Low profit, low popularity.

Beyond just classification, the platform provides specific recommendations for each item, such as price adjustments or description rewrites, to help improve overall restaurant margins.

## Features

### Manager Dashboard
*   **Performance Overview**: See key metrics like total profit and item counts at a glance.
*   **Category Breakdown**: Visual distribution of menu items (Stars, Plowhorses, etc.).
*   **Menu Management**: Add, edit, and remove menu items directly from the dashboard.

### AI & ML Capabilities
*   **Auto-Classification**: Automatically labels items based on sales volume and margin data.
*   **Smart Suggestions**: Provides actionable advice (e.g., "Increase price" or "Rename item") based on the item's classification.
*   **Description Enhancer**: Uses a Large Language Model (DeepSeek via OpenRouter) to rewrite menu descriptions, making them more appealing to customers.
*   **Daily Reports**: Generates a text summary of the day's performance and highlights offering specific business insights.

### Staff & Customer Views
*   **Staff Interface**: Simple order-taking screen for staff to log sales.
*   **Public Menu**: A clean, responsive digital menu for customers to browse.

## Technologies Used

### Backend
*   **Python & Django**: Main application logic and REST API.
*   **PostgreSQL**: Primary database for storing menu, user, and order data.
*   **Redis & Celery**: Handles background tasks, such as generating AI reports, to keep the application responsive.

### Frontend
*   **Next.js (React)**: User interface for both managers and customers.
*   **TypeScript**: Ensures type safety across the frontend code.
*   **Tailwind CSS**: Utility-first styling for a responsive design.

### AI / Data Science
*   **Scikit-Learn**: Used for the decision tree classifier to categorize menu items.
*   **DeepSeek (via OpenRouter)**: LLM used for generating text-based recommendations and description improvements.
*   **Pandas**: Data processing and analysis.

## Installation

### Prerequisites
*   Docker and Docker Compose
*   Git

### Setup Steps

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Start-Hack-2026/MenueEngineering.git
    cd MenueEngineering
    ```

2.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    OPENROUTER_API_KEY=your_key_here
    POSTGRES_DB=menu_engineering
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    ```

3.  **Start the Application**
    We use Docker Compose to run all services (Backend, Frontend, Database, Redis).
    ```bash
    # If using just
    just down; just up-build

    # Or standard docker-compose
    docker-compose down
    docker-compose up --build -d
    ```

4.  **Initialize the Database**
    Run the migrations to create the necessary tables.
    ```bash
    docker-compose exec backend python manage.py migrate
    ```

5.  **Create an Admin User**
    required to access the management dashboard.
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```

6.  **Access the App**
    *   **Dashboard**: [http://localhost:3000](http://localhost:3000)
    *   **API**: [http://localhost:8000/api](http://localhost:8000/api)

## Usage

1.  **Login**: Go to `http://localhost:3000` and log in with the superuser credentials you created.
2.  **Add Menu Items**: Use the "Menu Items" tab to populate your menu with dishes, prices, and costs.
3.  **Simulate Orders**: Use the Staff view (or create dummy data) to generate sales history.
4.  **Get Insights**:
    *   Go to the **Dashboard** to see items classified as Stars, Dogs, etc.
    *   Click **AI Report** to generate a written analysis.
    *   Check **Suggestions** for specific actions to improve menu performance.

## Team Members

*   **Hamdy El-Madbouly** - *Backend & AI Integration*
    *   Built the Django/FastAPI backend structure.
    *   Integrated the DeepSeek LLM APIs.
    *   Set up Celery/Redis for background processing.

*   **Radwa AbouElfotouh** - *Frontend Designer*
    *   Developed the Next.js frontend and dashboard UI.
    *   Designed the responsive layout for the customer menu.
    *   Assisted with database schema design.

*   **Hajar Sharqawy** - *Data Analyst*
    *   Led data cleaning and preprocessing efforts.
    *   Structured the dataset for the ML models.
    *   Helped design the decision tree logic.

*   **Malak** - *ML Engineer*
    *   Implemented the Decision Tree model for item classification.
    *   Tuned the model parameters for better accuracy.

*   **Alaa Amer** - *Business Analyst*
    *   Defined the business rules for menu engineering.
    *   Integrated psychological pricing factors into the AI prompts.
    *   Designed the business model and strategy.
