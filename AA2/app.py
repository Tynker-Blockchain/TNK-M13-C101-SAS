from flask import Flask, render_template, request, redirect, session
import os
from time import time
from wallet import Wallet
from wallet import Account
import firebase_admin
from firebase_admin import credentials
import plotly.graph_objs as go

import json

STATIC_DIR = os.path.abspath("static")

app = Flask(__name__, static_folder=STATIC_DIR)
app.use_static_for_root = True

myWallet = Wallet()
account = None
allAccounts = []
user = None
isSignedIn = False


def firebaseInitialization():
    cred = credentials.Certificate("config/serviceAccountKey.json")
    firebase_admin.initialize_app(
        cred,
        {"databaseURL": "https://blockchain-wallet-a2812-default-rtdb.firebaseio.com"},
    )
    print("🔥🔥🔥🔥🔥 Firebase Connected! 🔥🔥🔥🔥🔥")


firebaseInitialization()


@app.route("/", methods=["GET", "POST"])
def home():
    global myWallet, account, allAccounts, isSignedIn
    isConnected = myWallet.checkConnection()

    balance = "No Balance"
    transactions = None

    transactionData = {}
    balanceData = {}
    transactionDataPie = {}
    # Create a variable transactionDatadoughnut
    transactionDatadoughnut = {}
    # Create a variable sentBalance and set it 0 initially
    sentBalance = 0
    # Create a variable recivedblance and set it 0 initially
    recivedblance = 0

    if isSignedIn:
        allAccounts = myWallet.getAccounts()
        if account == None and allAccounts:
            account = allAccounts[0]

        if account:
            address = 0
            if type(account) == dict:
                balance = myWallet.getBalance(account["address"])
                transactions = myWallet.getTransactions(account["address"])
                address = account["address"]
            else:
                balance = myWallet.getBalance(account.address)
                transactions = myWallet.getTransactions(account.address)
                address = account.address

            amountList = []
            colorList = []
            indicesTransactions = []
            balanceList = [float(balance)]
            indicesBalance = [0]

            reverseTransactions = transactions[::-1]
            for index, transaction in enumerate(reverseTransactions):
                amountList.append(float(transaction["amount"]))
                colorList.append("red" if transaction["from"] == address else "blue")
                indicesTransactions.append(index)

            traceTnx = {
                "x": indicesTransactions,
                "y": amountList,
                "name": "Amount",
                "type": "bar",
                "marker": {"color": colorList},
            }

            layoutTnx = {
                "title": "Transaction History",
                "xaxis": {"title": "Transaction Index"},
                "yaxis": {"title": "Amount(ETH)"},
            }

            transactionData = {"trace": [traceTnx], "layout": layoutTnx}
            transactionData = json.dumps(transactionData)

            for index, transaction in enumerate(transactions):
                if transaction["from"] == address:
                    balance = float(balance) + float(
                        transaction["amount"]
                    ) 
                    # Add sent transaction amount of each transaction in sentBalance variable.
                    sentBalance += balance
                else:
                    balance = float(balance) - float(transaction["amount"])
                    # Add recived transaction amount of each transaction in recivedblance variable.
                    recivedblance += balance
                balanceList.append(balance)
                indicesBalance.append(index + 1)

            balanceList = balanceList[::-1]
            print(sentBalance)
            print(recivedblance)

            traceBalance = {
                "x": indicesBalance,
                "y": balanceList,
                "name": "Account Balance",
                "mode": "lines+markers",
                "line": {"color": "blue"},
                "marker": {"color": colorList},
            }
            layoutBalance = {
                "title": "Balance History",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Amount(ETH)"},
            }
            balanceData = {"trace": [traceBalance], "layout": layoutBalance}
            balanceData = json.dumps(balanceData)

            labels = ["Received", "Sent"]
            values = [
                sum(1 for color in colorList if color == "blue"),
                sum(1 for color in colorList if color == "red"),
            ]

            pie_data = {
                "labels": labels,
                "values": values,
                "type": "pie"
                }

            layoutPie = {
                "title": "Transaction History",
            }
            transactionDataPie = {"data": [pie_data], "layout": layoutPie}
            transactionDataPie = json.dumps(transactionDataPie)


            # Create example data lableD and valueD for the Doughnut chart
            labelD = ["Received", "Sent"]
            valueD = [ recivedblance, sentBalance]

            # Create a dictionary for the Doughnut chart data
            doughnut_data = {
                "labels": labelD,
                "values": valueD,
                "type": "pie",
                "hole": 0.5 # Set hole size to create a Doughnut chart

                }

            # Create layoutDoughnut
            layoutDoughnut = {
                "title": "Total Sent vs. Total Received",
            }

            # Create the Doughnut chart data dictionary
            transactionDatadoughnut = {"data": [doughnut_data], "layout": layoutDoughnut}

            # Convert the data to JSON
            transactionDatadoughnut = json.dumps(transactionDatadoughnut)


    # Pass the transactionDatadoughnut
    return render_template(
        "index.html",
        isConnected=isConnected,
        account=account,
        balance=balance,
        transactions=transactions,
        allAccounts=allAccounts,
        isSignedIn=isSignedIn,
        transactionData=transactionData,
        balanceData=balanceData,
        transactionDataPie=transactionDataPie,
        transactionDatadoughnut = transactionDatadoughnut
    )


@app.route("/makeTransaction", methods=["GET", "POST"])
def makeTransaction():
    global myWallet, account

    receiver = request.form.get("receiverAddress")
    amount = request.form.get("amount")

    privateKey = None
    if type(account) == dict:
        privateKey = account["privateKey"]
        sender = account["address"]
    else:
        privateKey = account.privateKey
        sender = account.address

    privateKey = account["privateKey"]

    tnxHash = myWallet.makeTransactions(sender, receiver, amount, privateKey)
    myWallet.addTransactionHash(tnxHash, sender, receiver, amount)
    return redirect("/")


@app.route("/createAccount", methods=["GET", "POST"])
def createAccount():
    global account, myWallet
    username = myWallet.username
    account = Account(username)
    return redirect("/")


@app.route("/changeAccount", methods=["GET", "POST"])
def changeAccount():
    global account, allAccounts

    newAccountAddress = int(request.args.get("address"))
    account = allAccounts[newAccountAddress]
    return redirect("/")


@app.route("/signIn", methods=["GET", "POST"])
def signIn():
    global account, allAccounts, isSignedIn, myWallet
    isSignedIn = True

    username = request.form.get("user")
    password = request.form.get("password")

    isSignedIn = myWallet.addUser(username, password)
    return redirect("/")


@app.route("/signOut", methods=["GET", "POST"])
def signOut():
    global account, allAccounts, isSignedIn
    isSignedIn = False
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=4000)
