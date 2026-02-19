# 📬 Leetcode-daily-problem-tracker

Automatically stay on top of your LeetCode journey!  
**Leetcode-daily-problem-tracker** sends friendly reminder emails to your registered email address about the LeetCode Daily Problem, helping you build a consistent problem-solving habit.

---

## 🚀 Introduction

**Leetcode-daily-problem-tracker** is a Python-based application that automates daily reminders for LeetCode's Daily Challenge. Once configured, you'll receive a timely email reminder with details about the day's problem—never miss a day in your coding practice!

---

## ✨ Features

- ⏰ **Daily Email Reminders**: Receive automatic emails about LeetCode’s Daily Problems.
- 📨 **Customizable Email Settings**: Register your email and manage reminders easily.
- 🔒 **Secure Authentication**: Uses OAuth 2.0 for safe access to email APIs.
- 📅 **Timezone Support**: Reminders are sent according to your preferred timezone.
- 🗃️ **Easy Setup**: Simple installation and configuration steps.

---

## 🛠️ Installation

1. **Clone the Repository**
    ```bash
    git clone https://github.com/pranesh-2005/Leetcode-daily-problem-tracker.git
    cd Leetcode-daily-problem-tracker
    ```

2. **Create & Activate a Virtual Environment (Optional but recommended)**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    > *Dependencies include: `pytz`, `psycopg2`, `requests`, `gradio`, `google-auth`, `google-api-python-client`, etc.*

4. **Set up Environment Variables**  
   Create a `.env` file and add your configuration (database URL, API keys, etc.).
   ```
   EMAIL_USER=your_email@example.com
   EMAIL_PASSWORD=your_password
   DATABASE_URL=your_database_url
   ```

---

## ▶️ Usage

1. **Run the Application**
    ```bash
    python app.py
    ```

2. **Register Your Email**
    - Follow the prompts in the Gradio UI or CLI to register your email address.
    - Set your timezone and preferences.

3. **Start Receiving Reminders**
    - The app will automatically fetch the LeetCode Daily Problem and send you a reminder email each day.

---

## 🤝 Contributing

Contributions are welcome!  
To contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Create a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

**Happy Coding!** 💻✨  
*Never miss a LeetCode Daily Problem again!*



## License
This project is licensed under the **MIT** License.

---
🔗 GitHub Repo: https://github.com/Pranesh-2005/Leetcode-daily-problem-tracker