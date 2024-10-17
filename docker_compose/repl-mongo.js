db = (new Mongo("localhost:27017")).getDB("test");
config = {
    "_id" : "oms-mongo-rset",
    "members" : [
    {
        "_id" : 0,
        "host" : "mongo1:27017"
    },
    {
        "_id" : 1,
        "host" : "mongo2:27017"
    }
  ]
};
rs.initiate(config);
