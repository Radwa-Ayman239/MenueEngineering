# Data Analysis & Engineering

This directory contains the data science work aimed at analyzing menu performance and developing the classification models.

## Structure

- **`Datasets/`**: Contains the raw and processed CSV files used for training and analysis.
  - `dim_menu_items_cleaned_predictions.csv`: The main dataset with engineered features.
  
- **Notebooks (`.ipynb`)**:
  - `Classification_Model_desion_tree.ipynb`: Development of the decision tree model for menu item classification.
  - `Classification_Model_desion_tree_Menu_Owner.ipynb`: Extended analysis for the business owner perspective.

## Purpose

The work here establishes the "Menu Engineering Matrix" logic—classifying items based on Profitability (Margin) and Popularity (Sales Volume). The logic derived here is implemented deterministically in the backend (`backend/menu/menu_classifier.py`).
