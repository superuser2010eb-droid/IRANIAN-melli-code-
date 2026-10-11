🇮🇷 Iranian Melli Code Analyzer Pro

🔍 Validate. Analyze. Visualize. Learn.

A modern Python desktop application for analyzing Iranian National ID codes — featuring checksum validation, batch processing, data visualization, and machine learning experiments.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GUI-Tkinter-FF9800?style=for-the-badge" alt="Tkinter">
  <img src="https://img.shields.io/badge/Machine%20Learning-Scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="Machine Learning">
  <img src="https://img.shields.io/badge/License-MIT-2EA44F?style=for-the-badge" alt="MIT License">
</p><p align="center">
  <b>A practical project at the intersection of Python, data analysis, algorithms, and machine learning.</b>
</p>---

✨ What Can It Do?

Iranian Melli Code Analyzer Pro brings multiple national ID code analysis tools together in one desktop application, with a tabbed interface designed for convenient everyday use and programming experimentation.

Feature| Description
🔍 ID Validation| Validate 10-digit Iranian national ID codes using the Mod-11 checksum algorithm.
📂 Batch Processing| Process lists of codes from TXT and CSV files.
⚙️ Code Generation| Generate checksum-valid test sequences within a configurable numeric range.
🧠 ML Experiments| Train a Linear Regression model on a supplied dataset and explore its predictions.
📅 Date Estimation| Experiment with model-based date estimates using suitable training data.
📊 Data Analytics| Explore prefix distributions and visualize results with charts.
🌙 Dark & Light Themes| Switch between dark and light interface modes.
📤 Export Support| Export generated results to supported text and spreadsheet formats.

🚀 Why This Project?

Instead of writing separate scripts for every task, this project combines useful tools in one place.

- One interface, multiple tools: Switch between validation, analysis, and visualization.
- Algorithm-focused: Explore checksum validation and numeric data processing.
- Data science practice: Experiment with regression models and dataset analysis.
- Beginner-friendly learning: A practical starting point for Python GUI development.
- Batch workflows: Work with multiple records instead of processing every entry manually.

🖥️ Preview

«Add a real screenshot of your application here to help visitors understand the interface at a glance.»

<!-- Replace the placeholder below with a screenshot committed to your repository. --><!-- Example: ![Application Preview](assets/screenshot.png) -->Tip: A screenshot showing the main window, dark theme, and validation results can make your repository much more appealing.

🛠️ Built With

- Python — core application logic
- Tkinter — desktop graphical interface
- Scikit-learn — machine learning experiments
- Pandas — tabular data processing, if used in the implementation
- Matplotlib — data visualization

📦 Getting Started

Requirements

- Python 3.8 or later
- pip
- The dependencies used by your project

Installation

Clone the repository:

git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_FOLDER

Install the dependencies listed in your project's "requirements.txt":

pip install -r requirements.txt

Run the application using your project's actual entry-point filename:

python main.py

«Replace the repository URL, folder name, and entry-point filename with the actual values from your project.»

🧪 How It Works

1. Checksum Validation

The validation module applies the Mod-11 checksum procedure to check whether a code satisfies the expected structural and checksum rules.

Important: Passing a checksum test does not prove that a national ID was officially issued or belongs to a real person.

2. Batch Analysis

Import supported files, process multiple entries, and review the resulting validation and analysis output.

3. Machine Learning Experiments

Load an appropriate dataset and train a regression model to investigate relationships between selected input features and target values.

Important: Iranian national ID numbers do not directly encode a person's date of birth. Any date prediction is a dataset-dependent experiment, not a reliable way to determine someone's actual birth date.

4. Data Visualization

Use charts to explore code-prefix distributions and identify patterns in your dataset.

🔐 Privacy & Responsible Use

This project is intended for education, software development, and authorized testing.

- Use synthetic or properly authorized test data.
- Treat checksum-valid sequences as test values, not verified identities.
- Do not use the application to identify people, infer sensitive personal information, or generate codes for impersonation.
- Review applicable privacy laws before processing personal information.

🗺️ Roadmap

Potential improvements for future releases:

- [ ] Add automated unit tests for checksum validation.
- [ ] Improve error handling for malformed input files.
- [ ] Add sample synthetic datasets for safe experimentation.
- [ ] Improve the graphical interface and accessibility.
- [ ] Add clearer analytics summaries and export options.
- [ ] Provide reproducible machine learning examples.
- [ ] Add screenshots and a short demonstration GIF.

🤝 Contributing

Contributions, bug reports, and feature suggestions are welcome!

1. Fork this repository.
2. Create a feature branch.
3. Make your changes and test them.
4. Open a pull request describing your contribution.

Please avoid committing real national ID numbers or other personal information.

⭐ Support the Project

If you find this project useful for learning Python, algorithms, or data analysis:

- ⭐ Star the repository.
- 🍴 Fork it and experiment with the code.
- 🐛 Report bugs and suggest improvements.
- 💡 Share ideas for future features.

Every constructive contribution helps the project grow!

📄 License

This project is distributed under the MIT License. See the "LICENSE" file for details.

---

<p align="center">
  <b>Made with Python 🐍 and a passion for automation 🇮🇷</b>
</p>
