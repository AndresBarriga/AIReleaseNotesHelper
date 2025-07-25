import csv

def load_tickets_from_csv(file_path, release_version):
    tickets = []
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('fixVersion') == release_version and row.get('Status') == 'Done':
                tickets.append(row)
    return tickets
