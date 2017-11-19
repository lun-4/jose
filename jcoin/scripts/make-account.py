import requests

def main():
    r = requests.post('http://0.0.0.0:8080/wallets/162819866682851329', json={
            'type': 0,
        })
    print(r)

if __name__ == '__main__':
    main()
