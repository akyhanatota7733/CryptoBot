import sqlite3 as sq

class Simple_DB:
    def __init__(self, file):
        self.conn = sq.connect(file, check_same_thread=False)
        self.cur = self.conn.cursor()

    def create_table(self, table, columns_parametrs):
        columns_parametrs = columns_parametrs.replace('; ',',\n')
        self.cur.execute('CREATE TABLE IF NOT EXISTS '+table+' ('+columns_parametrs+')')

    def select(self, request_text):
        request_text = request_text.split('; ',maxsplit=2)
        query = 'SELECT * FROM '+request_text[0]+' WHERE '+request_text[1]
        req = self.cur.execute(query)
        return req.fetchall()

    def delete(self, request_text):
        request_text = request_text.split('; ',maxsplit=2)
        query = 'DELETE FROM '+request_text[0]+' WHERE '+request_text[1]
        self.cur.execute(query)

    def insert(self, request_text):
        request_text = request_text.split('; ',maxsplit=3)
        request_text[1] = request_text[1].replace(' ',',\"')
        request_text[2] = request_text[2].replace(' ',',\"')
        value_to_insert = request_text[2].split(',\"')
        request_text[2]=''
        for i in range(len(value_to_insert)):
            if i != len(value_to_insert)-1:
                request_text[2]+=value_to_insert[i]+',\"'
            else:
                request_text[2]+=value_to_insert[i]
        query = 'INSERT INTO '+request_text[0]+' ('+request_text[1]+') VALUES ('+request_text[2]+')'
        self.cur.execute(query)

    def update(self, request_text):
        request_text = request_text.split('; ',maxsplit=4)
        value_to_insert = request_text[2].split(',')
        request_text[2]=''
        for i in range(len(value_to_insert)):
            if i != len(value_to_insert)-1:
                request_text[2]+=value_to_insert[i]+','
            else:
                request_text[2]+=value_to_insert[i]
        query = 'UPDATE '+request_text[0]+' SET '+request_text[1]+' = '+request_text[2]+' WHERE ' + request_text[3]
        self.cur.execute(query)
    def request(self, request_text): 
        req = self.cur.execute(request_text)   
        return req.fetchall()
    def commit(self): 
        self.conn.commit()  
    def close(self): 
        self.conn.close()
