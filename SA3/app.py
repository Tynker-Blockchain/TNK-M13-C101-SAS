from flask import Flask, render_template, request, redirect, session
import os
from time import time
from wallet import Wallet
from wallet import Account
import firebase_admin
from firebase_admin import credentials
import json

STATIC_DIR = os.path.abspath('static')

app = Flask(__name__, static_folder=STATIC_DIR)
app.use_static_for_root = True

myWallet =  Wallet()
account = None
allAccounts = []
user= None
isSignedIn = False

def firebaseInitialization():
    cred = credentials.Certificate("config/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://blockchain-wallet-a2812-default-rtdb.firebaseio.com'})
    print("🔥🔥🔥🔥🔥 Firebase Connected! 🔥🔥🔥🔥🔥")

firebaseInitialization()

@app.route("/", methods= ["GET", "POST"])
def home():
    global myWallet, account, allAccounts, isSignedIn
    isConnected = myWallet.checkConnection()
   
    balance = "No Balance"
    transactions = None
    
    transactionData = {}
    #SA3: Create a variable balanceData
    balanceData = {}

    if(isSignedIn):
        allAccounts = myWallet.getAccounts()
        if(account == None and allAccounts):
            account = allAccounts[0]

        if(account):
            address = 0
            if(type(account) == dict):
                balance = myWallet.getBalance(account['address'])
                transactions = myWallet.getTransactions(account['address'])
                address= account['address']
            else:
                balance = myWallet.getBalance(account.address)
                transactions = myWallet.getTransactions(account.address)
                address= account.address

            amountList = []
            colorList=[]
            indicesTransactions = []

            # SA3: Create balanceList and add current balance as first entry in float type
            balanceList=[float(balance)]
            # SA3: Create indicesBalance and add 0 as first entry
            indicesBalance = [0]
            

            reverseTransactions = transactions[::-1]
            for index, transaction in enumerate(reverseTransactions):
                amountList.append(float(transaction["amount"]))
                colorList.append("red" if transaction["from"] == address else "blue")
                indicesTransactions.append(index)
                
            traceTnx = {
                'x': indicesTransactions,
                'y': amountList,
                'name': 'Amount',
                'type': 'bar',
                'marker': { 'color' : colorList }
            }
    
            layoutTnx = {
                'title': 'Transaction History',
                'xaxis': { 'title': 'Transaction Index' },
                'yaxis': { 'title': 'Amount(ETH)' }
            }

            transactionData ={
                 'trace': [traceTnx], 
                 'layout': layoutTnx
                 }
            
            transactionData = json.dumps(transactionData)

            # SA3: Creating list of balance history
            for index, transaction in enumerate(transactions):
                # SA3: Check if transaction['from'] == address and add or subtract the transaction amount from balance to get balance
                if transaction['from'] == address:
                    balance = float(balance) + float(transaction['amount']) #+ 0.021  # Assuming gas fee
                else:
                    balance = float(balance) - float(transaction['amount'])
                # SA3: Append balance to balance list    
                balanceList.append(balance)
                # SA3: Append index+1 to indicesBalance
                indicesBalance.append(index+1)
            
            # SA3: Reverse the balance list
            balanceList = balanceList[::-1]

            # SA3: Create traceBalance
            traceBalance= {
                    'x': indicesBalance,
                    'y': balanceList,
                    'name': 'Account Balance',
                    'mode': 'lines+markers', 
                    'line': {
                        'color': 'blue'
                    },
                    'marker': {
                        'color': colorList
                    }
                }
            # SA3: Create layoutBalance
            layoutBalance = {
                    'title': 'Balance History',
                    'xaxis': { 'title': 'Time' },
                    'yaxis': { 'title': 'Amount(ETH)' },
                }
            # SA3: Create balanceData
            balanceData ={
                 'trace': [traceBalance], 
                 'layout': layoutBalance
                 }
            # SA3: Convert balanceData to json
            balanceData = json.dumps(balanceData)

    #SA3: return balanceData as balanceData
    return render_template('index.html', 
                        isConnected=isConnected,  
                        account= account, 
                        balance = balance, 
                        transactions = transactions, 
                        allAccounts=allAccounts,
                        isSignedIn = isSignedIn,
                        transactionData = transactionData,
                        balanceData = balanceData )



@app.route("/makeTransaction", methods = ["GET", "POST"])
def makeTransaction():
    global myWallet, account

    receiver = request.form.get("receiverAddress")
    amount = request.form.get("amount")

    privateKey = None
    if(type(account) == dict):
            privateKey = account['privateKey']
            sender= account['address']
    else:
            privateKey = account.privateKey
            sender= account.address

    privateKey = account['privateKey']

    tnxHash = myWallet.makeTransactions(sender, receiver, amount, privateKey)
    myWallet.addTransactionHash(tnxHash, sender, receiver,amount)
    return redirect("/")


@app.route("/createAccount", methods= ["GET", "POST"])
def createAccount(): 
    global account, myWallet
    username = myWallet.username
    account = Account(username)
    return redirect("/")

@app.route("/changeAccount", methods= ["GET", "POST"])
def changeAccount(): 
    global account, allAccounts
    
    newAccountAddress = int(request.args.get("address"))
    account = allAccounts[newAccountAddress]
    return redirect("/")

@app.route("/signIn", methods= ["GET", "POST"])
def signIn(): 
    global account, allAccounts, isSignedIn, myWallet
    isSignedIn = True
    
    username = request.form.get("user")
    password = request.form.get("password")
    
    isSignedIn = myWallet.addUser(username, password)
    return redirect("/")

@app.route("/signOut", methods= ["GET", "POST"])
def signOut(): 
    global account, allAccounts, isSignedIn
    isSignedIn = False
    return redirect("/")

if __name__ == '__main__':
    app.run(debug = True, port=4000)



