from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder='templates1')


# Temporary data (replace with database later)
news_data = [
    {"title": "Kenya wins AFCON", "category": "Sports", "content": "Kenya has made history...", "link": "https://example.com"},
    {"title": "Budget 2025 Released", "category": "Politics", "content": "The 2025 budget is out...", "link": "https://example.com"},
]

@app.route('/')
def index():
    query = request.args.get('search', '').lower()
    category = request.args.get('category', '')

    filtered_news = [
        item for item in news_data
        if (query in item['title'].lower()) and
           (category == '' or item['category'] == category)
    ]

    categories = sorted(set(item['category'] for item in news_data))
    return render_template('index.html', news=filtered_news, categories=categories)

@app.route('/add', methods=['GET', 'POST'])
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        content = request.form['content']
        link = request.form['link']

        new_article = {
            "title": title,
            "category": category,
            "content": content,
            "link": link
        }

        news_data.append(new_article)  # Temporary, for testing
        return redirect(url_for('index'))

    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)
