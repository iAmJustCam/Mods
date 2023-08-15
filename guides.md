---

### **Configuration Guide**

---

#### **Introduction**:
The `config.ini` file plays a pivotal role in `Mods`, allowing users to tweak settings to their preferences. This file contains various sections, each with its set of configurations.

#### **Scoring Criteria**:
To modify how points are awarded to teams based on their stats, you can adjust the scoring criteria in the `config.ini` file.

```ini
[Scoring]
home_team_advantage = 3
point_difference_threshold = 5
```

For instance, if you want to give the home team a 5-point advantage, simply change the `home_team_advantage` value to 5.

#### **Team Name Mappings**:
Team names might differ across data sources. The `config.ini` file allows you to map these names for consistency.

```ini
[TeamNames]
LAL = Los Angeles Lakers
BOS = Boston Celtics
```

To add a new team, simply append its abbreviation and full name to the `[TeamNames]` section.

#### **Logging Levels**:
Control the verbosity of logs by adjusting the logging level.

```ini
[Logging]
level = DEBUG
```

Available levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. For regular use, `INFO` is recommended.

---

### **Developer's Corner**

---

#### **Project Architecture**:
`Mods` is modular, with each module handling a specific task. For instance, the `fetcher.py` module is responsible for data fetching.

```python
from fetcher import DataFetcher
fetcher = DataFetcher()
data = fetcher.get_data(url)
```

#### **Setting Up a Development Environment**:
To set up a local development environment, it's recommended to use virtual environments.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **Code Standards**:
Always follow PEP 8 standards. For instance, function names should be lowercase with underscores.

```python
def fetch_data(url):
    pass
```

#### **Contribution Guidelines**:
After forking and cloning the repository, create a new branch for your feature or fix.

```bash
git checkout -b feature/new-feature
```

---

### **User Handbook**

---

#### **Getting Started**:
`Mods` is designed for ease of use. Once set up, you can start backtesting with just a few commands.

#### **Installation & Setup**:
After cloning the repository, navigate to the project directory and install the required packages.

```bash
cd Mods
pip install -r requirements.txt
```

#### **Running Your First Backtest**:
Starting a backtest is as simple as running the main script.

```bash
python main.py
```

You'll be prompted to enter a backtest period. For the default 7-day period, simply press enter.

#### **Advanced Usage**:
For users interested in diving deeper, `Mods` offers advanced features. For instance, to adjust the scoring criteria, modify the `config.ini` file as explained in the Configuration Guide.

#### **Troubleshooting**:
If you encounter issues, check the `log.txt` file for detailed error messages. This can provide insights into what might have gone wrong.

```bash
cat log.txt
```

---

These expanded guides with code snippets and examples aim to provide a clearer understanding of how to use and modify `Mods`. They cater to both regular users and developers, ensuring that all potential questions and use cases are addressed.