import yaml
import datetime

# 出力先ファイル
outjp = "content/research.md"
outen = "content/en/research.md"
# outjp = "test/researchjp.md"
# outen = "test/researchen.md"

# データファイル
publication_db = "data/publications.yml"

def print_journal(x, out):
    # title = x['title'].capitalize() 
    # MSO とかでダメになる
    title = x['title']
    out.write('1. ')
    out.write(', '.join(x['author']) + '. ')
    out.write(title + '. ')
    out.write('_' + x['journal'] + '_, ')
    out.write(x['volume'] + ', ')
    out.write('pp. ' + x['pages'] + '. ')
    out.write(x['year'] + '. ')
    if 'doi' in x:
        out.write("[[📖doi link]("+ x['doi'] +")]")
    if 'arxiv' in x:
        out.write("[[📝arXiv]("+ x['arxiv'] +")]")
    out.write('\n')

def print_conference(x, out):
    # title = x['title'].capitalize()
    title = x['title']
    out.write('1. ')
    # if title in jtitle:
    #     out.write('[[Link to journal ver](#j' + jtitle[title] + ')]')

    out.write(', '.join(x['author']) + '. ')
    out.write(title + '. ')
    out.write('_' + x['booktitle'] + '_. ')
    out.write(x['place'] + '. ')
    if 'series' in x:
        out.write(x['series'] + ', ' + x['volume'] + ', pp. ' + x['pages'] + '. ')
    else:
        out.write('accepted. ')
    out.write(x['year'] + ', ' + x['month'] + '. ')

    if 'doi' in x:
        out.write("[[📖doi link]("+ x['doi'] +")]")
    if 'arxiv' in x:
        out.write("[[📝arXiv]("+ x['arxiv'] +")]")
    out.write('\n')

def print_domestic(x, out):
    out.write('1. ')
    # pp = x['presenter']
    
    out.write(', '.join(x['author']) + '. ')
    out.write(x['title'] + '. ')
    out.write(', '.join(x['booktitle']) + '.\n')


with open(outjp, mode='w') as wjp, open(outen, mode='w') as wen:
    wjp.write(
        '---\ntitle: "研究成果"\nsummary: "研究成果"\ndate: ' + 
        datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00") + '\n---\n'
    )
    wen.write(
        '---\ntitle: "My publications"\nsummary: "My publications"\ndate: ' + 
        datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00") + '\n---\n'
    )

    with open(publication_db, mode='r') as cdb:
        db = yaml.safe_load(cdb)
        wjp.write("### Journal papers\n")
        wen.write("### Journal papers\n")
        for x in db["journal"]:
            print_journal(x, wjp)
            print_journal(x, wen)

        wjp.write("### Conference papers\n")
        wen.write("### Conference papers\n")
        for x in db["conference"]:
            print_conference(x, wjp)
            print_conference(x, wen)

        wjp.write("### 国内研究会発表\n")
        for x in db["domestic"]:
            print_domestic(x, wjp)

