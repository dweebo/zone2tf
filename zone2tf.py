import sys
import json


def gen_zone(**d):
    return '''
resource "aws_route53_zone" "{root_zone_name}" {{
  name = "{root_zone}"
}}'''.format(**d)

def gen_record(**d):
    return '''
resource "aws_route53_record" "{tf_name}" {{
  zone_id = aws_route53_zone.{root_zone_name}.id
  name    = "{record_name}"
  type    = "{type}"
  records = {records}
  ttl     = {ttl}
}}'''.format(**d)

if len(sys.argv) < 2:
    print("Usage:\n{0} <zonefile>".format(sys.argv[0]))
    exit(1)

with open(sys.argv[1], 'r') as zone_file:
    records = []
    root_zone = ''

    for line in zone_file:

        # skip line if it's not a record
        if ' IN ' not in line or line.startswith(';'):
            continue

        parts = line.split(' ')

        # try and find the root zone
        if parts[3] == 'SOA':
            root_zone = parts[0]
            root_zone_name = root_zone.replace('.','')

            print(gen_zone(root_zone=root_zone,
                           root_zone_name=root_zone_name))
            continue

        record_type = parts[3]

        # remove newline and white characters from record
        # and expand to include the rest of line if type can include spaces
        if record_type in ('MX', 'SRV', 'TXT'):
            record = ' '.join(parts[4:]).strip()
        else:
            record = parts[4].strip()

        # strip the root zone from the end of the string
        if parts[0].endswith('.{0}.'.format(root_zone)):
            record_name = parts[0][:-(len(root_zone) + 2)]
        else:
            record_name = parts[0]

        # strip double quotes if type is txt
        if record_type == 'TXT' and parts[4].startswith('"'):
            record = record[1:-1]

        record_ttl = int(parts[1])
        found = False
        for r in records:
            if r["record_name"] == record_name and r["record_type"] == record_type:
                found = True
                r["records"].append(record)
        if not found:
            records.append({
                "tf_name":'{0}-{1}'.format(parts[0].replace('.',''),parts[3].lower()),
                "record_name":record_name,
                "record_type":record_type,
                "record_ttl":record_ttl,
                "record_ttl":record_ttl,
                "records":[ record ],
                "root_zone_name":root_zone_name
            })

    for record in records:
        print(gen_record(tf_name=record["tf_name"],
                         record_name=record["record_name"],
                         ttl=record["record_ttl"],
                         type=record["record_type"],
                         records=json.dumps(record["records"]),
                         root_zone_name=record["root_zone_name"]))
