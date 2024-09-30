from flask import Flask, request, render_template_string
import re

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def convert_text():
    if request.method == 'POST':
        input_text = request.form.get('text')
        converted_text = convert_text_with_regex(input_text)
        return render_template_string('''
            <form method="POST">
                <label for="text">Zadejte text:</label><br>
                <textarea id="text" name="text" rows="4" cols="50">{{ input_text }}</textarea><br>
                <input type="submit" value="Převést">
            </form>
            <h2>Výsledek:</h2>
            <p>{{ converted_text }}</p>
        ''', input_text=input_text, converted_text=converted_text)
    else:
        return render_template_string('''
            <form method="POST">
                <label for="text">Zadejte text:</label><br>
                <textarea id="text" name="text" rows="4" cols="50"></textarea><br>
                <input type="submit" value="Převést">
            </form>
        ''')

def convert_text_with_regex(input_text):
    # Dictionary for number to letter conversion
    number_to_letter = {
        '1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e',
        '6': 'f', '7': 'g', '8': 'h', '9': 'i', '0': 'j'
    }

    # Function to replace digit sequences with '1' prefix and corresponding letters
    def replace_digits(match):
        return '1' + ''.join(number_to_letter.get(digit, digit) for digit in match.group(0))

    # Regex to find sequences of digits and replace them
    input_text = re.sub(r'\d+', replace_digits, input_text)

    # Function to process uppercase letters
    def process_uppercase(match):
        word = match.group(1)
        character_after = match.group(2)
        if len(word) > 1:  # It's a sequence of uppercase letters
            end_character = "2" if (character_after.islower()) else ""
            return '4' + word.lower() + end_character + character_after
        else:  # Single uppercase letter
            return '3' + word.lower()+ character_after

    # Regex to handle sequences of uppercase letters or single uppercase letters
    input_text = re.sub(r'\b([A-Z]+)(.)', process_uppercase, input_text)  # For isolated uppercase words

    return input_text

if __name__ == '__main__':
    app.run(debug=True)
