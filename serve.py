from flask import Flask, render_template, request, jsonify
from scripts import get_one, get_all, txt_to_num, alnum_to_num

NUMS = sorted(get_all())

app = Flask(__name__)

@app.route('/')
def index():
    # Pass list of dicts with the data we need
    constant_data = [
        {
            'name': c.name,
            'base': c.base,
            'format': c.format,
            'size': c.size,
            'display': str(c)  # __repr__ for display
        }
        for c in NUMS
    ]
    print(constant_data)
    return render_template('index.html', constants=constant_data)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    name = request.args.get('name', '')
    base = request.args.get('base', '')
    size = request.args.get('size', '')
    format_type = request.args.get('format', '')
    
    if not query or not name:
        return jsonify({'result': ''})
    
    try:
        constant = list(filter(lambda n:all((n.name==name, n.base==int(base), n.format==format_type, n.size==int(size))), NUMS))
        if not constant:
            return jsonify({'result': 'Constant not found'})
        constant = constant[0]
        if format_type == "txt":
            if query.isalpha():
                query = txt_to_num(query)
            if query.isalnum():
                query = alnum_to_num(query)
        result = constant[query]
        if result != -1:
            arround = constant[result-6 : result+4+len(query)].decode()
        else:
            arround = ""
        return jsonify({'query':f"{query} ({query.encode()})", 'result': result, 'arround':arround})
    except (KeyError, Exception) as e:
        print(e)
        return jsonify({'result': f'Not found'})

if __name__ == '__main__':
    app.run(debug=True)
