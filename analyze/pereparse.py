import csv

def to_float(s:str):
    new_s = ''.join(s.split(' '))
    arr = new_s.split(',')
    return float(arr[0] + '.' + arr[1])

if __name__ == "__main__":

    fieldnames = []
    data = None

    with open('data.csv', "r",encoding='utf-8') as csv_reader:
        data = csv.DictReader(csv_reader, delimiter=',')
        new_data = []
        count = 0
        for row in data: 
            if count == 0:
                fieldnames = [i for i in row]

            if (not 'низкий' in row['оценка']) and (not 'средний' in row['оценка']) and (not 'высокий' in row['оценка']):
                del row
                continue

            for i in row:
                if i != 'инн' and i != 'год' and i!='оценка' and i!='дата_регистрации' and i!='статус':
                    row[i] = to_float(row[i])


            values = [row[i] for i in row]
            inner_dict = dict(zip(fieldnames, values))
            new_data.append(inner_dict)
            count += 1
        
        data = new_data
        csv_reader.close()
    
    with open('newdata.csv', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        print("FINISH!!!!")
        csv_file.close()
            
        