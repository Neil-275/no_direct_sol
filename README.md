# Math Tutor Chatbot with Multi-Agent System

This project is a Streamlit-based web application that provides an interactive math tutoring experience in Vietnamese. The core of the system leverages **LangGraph** to orchestrate a multi-agent architecture, enabling collaborative and context-aware problem solving.
## Key Features

- **Multi-Agent System with LangGraph**: Utilizes LangGraph to coordinate multiple AI agents, each specializing in different aspects of math tutoring (e.g., problem understanding, hint generation, solution verification).
- **Multipage Streamlit App**: Includes a home page and additional pages for tutoring and storage.
- **AI-Powered Tutoring**: Integrates with OpenAI's GPT models and custom APIs for math problem solving and tutoring.
- **Prompt Engineering**: Uses carefully crafted prompts to guide the AI's teaching style.
- **Session Memory**: Remembers conversation history for context-aware responses.
- **LaTeX Support**: Automatically converts LaTeX math expressions to Markdown for better display.
## Folder Structure

```
.
├── index.py                # Main entry point (home page)
├── pages/
│   ├── Bot_dạy_học.py      # Math tutor chatbot interface
│   └── Lưu_trữ.py          # Storage page (placeholder)
├── prompts/
│   └── prompts.py          # Prompt templates for AI
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Streamlit configuration
├── .gitignore
└── README.md
```
## Setup

1. **Clone the repository** and navigate to the project folder.

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Set up environment variables**:
    - Create a `.env` file in the root directory.
    - Add your API keys and endpoints:
      ```
      OPENAI_API_KEY=your_openai_api_key
      MATH_SOLVER=your_math_solver_api_endpoint
      MATH_TUTOR=your_math_tutor_api_endpoint
      ```

4. **Run the app**:
    ```sh
    streamlit run index.py
    ```
## Usage

- Open the app in your browser.
- Enter your OpenAI API key on the home page.
- Navigate to the "Bot dạy học" page to interact with the math tutor chatbot.

## Notes

- The app is designed for educational purposes and currently supports Vietnamese language interactions.
- Ensure your API endpoints for math solving and tutoring are running and accessible.
- **LangGraph** is central to the system, enabling robust multi-agent collaboration for enhanced tutoring.

