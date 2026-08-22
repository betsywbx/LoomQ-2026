from flask import Flask

# 1. 创建一个 Flask 应用实例
app = Flask(__name__)

# 2. 定义路由：当用户访问网站根目录 "/" 时，执行下面的函数
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# 3. 启动应用
if __name__ == "__main__":
    app.run(debug=True)