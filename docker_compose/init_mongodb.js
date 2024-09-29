db = db.getSiblingDB("order_matching_system"); // use db

// Stock Table (Collections/Structures)
db.createCollection('stock');
db.stock.ensureIndex({'stock_id': 1}, {unique: true}); // create unique constraint
db.stock.insertOne({'stock_id': 'apple'  , 'short': 'Apple Inc'  , 'isin': 'US0378331005', 'status': 'Active'})
db.stock.insertOne({'stock_id': 'amazon' , 'short': 'Amazon'     , 'isin': 'US0231351067', 'status': 'Active'})
db.stock.insertOne({'stock_id': 'zomato' , 'short': 'Zomato'     , 'isin': 'INE758T01015', 'status': 'Active'})

// Accounts Table
db.createCollection('account');
db.account.ensureIndex({'account_id': 1}, {unique: true}); // create unique constraint
db.account.insertOne({'account_id': 'a1', 'name': 'Name One'  , 'broker': 'Zerodha', 'CDSL' : '12341', 'segment': ['Equity', 'Derivatives']})
db.account.insertOne({'account_id': 'a2', 'name': 'Name Two'  , 'broker': 'SBIStoc', 'CDSL' : '12342', 'segment': ['Equity', 'Derivatives']})
db.account.insertOne({'account_id': 'a3', 'name': 'Name Three', 'broker': 'Zerodha', 'CDSL' : '12343', 'segment': ['Equity', 'Derivatives']})
db.account.insertOne({'account_id': 'a4', 'name': 'Name Four' , 'broker': 'Prostoc', 'CDSL' : '12344', 'segment': ['Equity', 'Derivatives']})

// Stock Order Table
db.createCollection('stock.order.apple');
db.createCollection('stock.order.amazon');
db.createCollection('stock.order.zoomato');
db.stock.order.apple.ensureIndex({'order_id': 1}, {unique: true}); // create unique constraint
db.stock.order.amazon.ensureIndex({'order_id': 1}, {unique: true}); // create unique constraint
db.stock.order.zoomato.ensureIndex({'order_id': 1}, {unique: true}); // create unique constraint

// Stock Audit Table
//db.createCollection('stock.audit.apple');
//db.createCollection('stock.audit.amazon');
//db.createCollection('stock.audit.zoomato');
//db.stock.audit.apple.ensureIndex({'order_id': 1, 'status': 1, 'trade_quantity': 1, 'trade_price': 1, 'timestamp': 1}, {unique: true}); // create unique constraint
//db.stock.audit.amazon.ensureIndex({'order_id': 1, 'status': 1, 'trade_quantity': 1, 'trade_price': 1, 'timestamp': 1}, {unique: true}); // create unique constraint
//db.stock.audit.zoomato.ensureIndex({'order_id': 1, 'status': 1, 'trade_quantity': 1, 'trade_price': 1, 'timestamp': 1}, {unique: true}); // create unique constraint

// Stock Trade Table
db.createCollection('stock.trade.apple');
db.createCollection('stock.trade.amazon');
db.createCollection('stock.trade.zoomato');
db.stock.trade.apple.ensureIndex({'trade_id': 1}, {unique: true}); // create unique constraint
db.stock.trade.amazon.ensureIndex({'trade_id': 1}, {unique: true}); // create unique constraint
db.stock.trade.zoomato.ensureIndex({'trade_id': 1}, {unique: true}); // create unique constraint

/*
order_id, user1, apple, 10, buy, 222
    Based on input --
        order_id is created
    Based on ticket -- queue/topic/channel is decided -- one channel is for one spark worker for one

user2, amazon, 1000, sell, 186
user3, amazon, 500, sell, 187
user4, ibm, 200, buy, 215
*/
