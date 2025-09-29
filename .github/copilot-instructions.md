# AI Coding Agent Instructions for This Codebase

Welcome to the `second-draft` Streamlit project! This document provides essential guidance for AI coding agents to be productive in this codebase. Follow these instructions to understand the architecture, workflows, and conventions specific to this project.

## Project Overview
This project is a Streamlit application designed for interactive data visualization and user interaction. The main entry point is `app.py`, which defines the app's layout and functionality.

### Key Files
- **`app.py`**: The main application file. Contains the Streamlit app logic, including layout, widgets, and callbacks.
- **`requirements.txt`**: Lists the Python dependencies required to run the application.
- **`logo.png`**: A static asset used in the application.
- **`.streamlit/config.toml`**: Configuration file for Streamlit settings (e.g., theme, server options).

## Developer Workflows

### Running the Application
To start the Streamlit app locally, use the following command:
```bash
streamlit run app.py
```
Ensure all dependencies in `requirements.txt` are installed beforehand:
```bash
pip install -r requirements.txt
```

### Debugging
- Use Streamlit's built-in debugging tools, such as `st.write()` and `st.error()`, to inspect variables and catch errors.
- Check the terminal output for logs when running the app.

### Testing
Currently, there are no automated tests in this codebase. If adding tests, consider using `pytest` and placing test files in a `tests/` directory.

## Project-Specific Conventions
- **Streamlit Patterns**: Follow Streamlit's idiomatic patterns for creating widgets and handling user input. For example:
  ```python
  import streamlit as st

  st.title("My App")
  name = st.text_input("Enter your name:")
  if name:
      st.write(f"Hello, {name}!")
  ```
- **Configuration**: Use `.streamlit/config.toml` to manage app-wide settings like themes and server options.

## External Dependencies
- **Streamlit**: The core framework for building the app.
- Additional dependencies are listed in `requirements.txt`. Ensure these are up-to-date and compatible.

## Integration Points
- **Static Assets**: Place images and other static files in the root directory or a dedicated `assets/` folder if needed.
- **Configuration**: Modify `.streamlit/config.toml` for Streamlit-specific settings.

## Suggestions for AI Agents
- When modifying `app.py`, ensure changes align with Streamlit's best practices.
- If adding new dependencies, update `requirements.txt` and verify compatibility.
- Document any new features or workflows in this file or a `README.md`.

---

If any section is unclear or incomplete, please provide feedback to improve this document.