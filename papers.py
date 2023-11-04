import yaml
import datetime

# 出力先ファイル
outjp = "content/research.md"
outen = "content/en/research.md"
# outjp = "test/researchjp.md"
# outen = "test/researchen.md"

# データファイル
publication_data = "data/publications.yml"


def author_mark(x):
    if 'presenter' in x:
        pp = x['presenter']
        ppidx = x['author'].index(pp)
        x['author'][ppidx] = '__*' + pp + '__'

def create_journal_list(xd) -> [str]:
    jlist = []
    for x in xd:
        title = x['title']
        paper = ', '.join(x['author']) + '.<br>' + title + '.<br>' +  '_' + x['journal'] + '_, '
        if 'volume' in x:
              paper += x['volume'] + ', '
        if 'pages' in x:
              paper += 'pp. ' + x['pages'] + '. '
        if 'year' in x:
              paper += x['year'] + '. '
        if 'doi' in x:
            paper += "[[📕doi]("+ x['doi'] +")]"
        if 'arxiv' in x:
            paper += "[[📝arXiv]("+ x['arxiv'] +")]"
        jlist.append(paper)
    return jlist

def create_preprint_papers(xd) -> [str]:
    jlist = []
    for x in xd:
        title = x['title']
        paper = ', '.join(x['author']) + '.<br>' + title + '.<br>'
        if 'doi' in x:
            paper += "[[📕doi]("+ x['doi'] +")]"
        if 'arxiv' in x:
            paper += "[[📝arXiv]("+ x['arxiv'] +")]"
        jlist.append(paper)
    return jlist

def create_conference_list(xd) -> [str]:
    clist = []

    for x in xd:
        title = x['title']
        author_mark(x)
        paper = ', '.join(x['author']) + '. <br>' + title + '.<br>'\
              +  '_' + x['booktitle'] + '_, '\
              + x['place'] + ', '
        if 'series' in x:
            paper += x['series'] + ', ' + x['volume'] + ', pp. ' + x['pages'] + '. '
        else:
            paper += 'accepted. '
        paper += x['month'] + ', ' + x['year'] + '. '
        if 'doi' in x:
            paper += "[[📘doi]("+ x['doi'] +")]"
        if 'arxiv' in x:
            paper += "[[📝arXiv]("+ x['arxiv'] +")]"
        clist.append(paper)
    return clist


def create_domestic(xd) -> ([str], int):
    dlist = []
    myname = "儀間 達也"
    count = 0

    for x in xd:
        author_mark(x)
        paper = ', '.join(x['author']) + '.<br>' + x['title'] + '.<br>'
        if myname == x['presenter']:
            count += len(x['booktitle'])
        for t in x['booktitle']:
            dlist.append(paper + t )
    return dlist, count

# main part 

with open(outjp, mode='w') as wjp, open(outen, mode='w') as wen:
    nowdate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    wjp.write(
        '---\ntitle: "研究成果"\nsummary: "研究成果"\ndate: ' + 
        nowdate + '\nmath: true\n'
         '\nShowToc: true\n---\n'
    )
    wen.write(
        '---\ntitle: "My publications"\nsummary: "My publications"\ndate: ' + 
        nowdate + '\nmath: true\n'
        '\nShowToc: true\n---\n'
    )

    wjp.write('最終更新日: ' +
     datetime.datetime.now().strftime("%Y年 %m月 %d日") +
      '\n\n'
    )
    wen.write('Last update: ' +
     datetime.datetime.now().strftime("%B, %d, %Y") +
      '\n\n'
    )
    wjp.write('[DBLP](https://dblp.org/pid/281/6848.html)\n')
    wen.write('[DBLP](https://dblp.org/pid/281/6848.html)\n')
    with open(publication_data, mode='r') as cd:
        db = yaml.safe_load(cd)

        # Journal
        wjp.write("### Journal papers\n")
        wen.write("### Journal papers\n")
        jlist = create_journal_list(db['journal'])
        for x in jlist:
            paper = '1. ' + x
            wjp.write(paper + '\n')
            wen.write(paper + '\n')
        # reversed ordered list
        wjp.write('{reversed="reversed"}\n')
        wen.write('{reversed="reversed"}\n')


        # Conference
        wjp.write("### Conference papers\n")
        wen.write("### Conference papers\n")
        clist = create_conference_list(db['conference'])
        for x in clist:
            paper = '1. ' + x
            wjp.write(paper + '\n')
            wen.write(paper + '\n')
        wjp.write('{reversed="reversed"}\n')
        wen.write('{reversed="reversed"}\n')

        # Workshop
        wjp.write("### 国際ワークショップでの発表\n")
        wen.write("### Presentations on International Workshops\n")
        clist = create_conference_list(db['workshop'])
        for x in clist:
            paper = '1. ' + x
            wjp.write(paper + '\n')
            wen.write(paper + '\n')
        wjp.write('{reversed="reversed"}\n')
        wen.write('{reversed="reversed"}\n')

        # preprints
        wjp.write("### プレプリント\n")
        wen.write("### Preprint papers\n")
        clist = create_preprint_papers(db['arxiv'])
        for x in clist:
            paper = '1. ' + x
            wjp.write(paper + '\n')
            wen.write(paper + '\n')
        wjp.write('{reversed="reversed"}\n')
        wen.write('{reversed="reversed"}\n')


        wjp.write("### 国内研究会\n")
        dlist, count = create_domestic(db["domestic"])
        wjp.write("儀間発表 " + str(count) + "件\n")
        for x in dlist:
            paper = '1. ' + x
            wjp.write(paper + '\n')
        wjp.write('{reversed="reversed"}\n')

