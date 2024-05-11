from datetime import datetime

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


with open('alex.log', 'a') as f:
    f.write(f'Hello {now}\n')

