import yaml
import datetime

# 出力先ファイル
out= "list.tex"
template= "template.tex"

# データファイル
publication_data = "data/publications.yml"

def author_mark(x):
    pp = x.get('presenter')
    if pp in x['author']:
        ppidx = x['author'].index(pp)
        x['author'][ppidx] = '*' + pp + ''

    for name in {'Tatsuya Gima', "儀間 達也"}:
        if name in x['author']:
            idx = x['author'].index(name)
            x['author'][idx] = '\\underline{' + x['author'][idx] + '}'
        name = '*' + name
        if name in x['author']:
            idx = x['author'].index(name)
            x['author'][idx] = '\\underline{' + x['author'][idx] + '}'

def create_journal_list(xd) -> [str]:
    jlist = []
    for x in xd:
        title = x['title']
        author_mark(x)
        paper = ', '.join(x['author']) + '.\n\t``' + title + ".''\n\t"
        if 'journal' in x:
            paper += '\\textit{' + x['journal'] + '}, '
        if 'volume' in x:
            paper += str(x['volume']) + ', '
        if 'pages' in x:
            paper += f"pp. {x['pages']}. "
        if 'year' in x:
            paper += str(x['year']) + '. '
        if 'doi' in x:
            paper += '\\url{' + x['doi'] +"}"
        jlist.append(paper)
    return jlist

# def create_preprint_papers(xd) -> [str]:
#     jlist = []
#     for x in xd:
#         title = x['title']
#         paper = ', '.join(x['author']) + '.<br>' + title + '.<br>'
#         if 'doi' in x:
#             paper += "[[📕doi]("+ x['doi'] +")]"
#         if 'arxiv' in x:
#             paper += "[[📝arXiv]("+ x['arxiv'] +")]"
#         jlist.append(paper)
#     return jlist

def create_conference_list(xd) -> [str]:
    clist = []

    for x in xd:
        title = x['title']
        author_mark(x)
        paper = ', '.join(x['author']) + '.\n\t``' + title + ".''\n\t"
        if 'booktitle' in x:
            paper += '\\textit{' + x['booktitle'] + '}, '
        if 'place' in x:
            paper += x['place'] + '. '
        proceedings = [str(x[field]) for field in ('series', 'volume') if field in x]
        if 'pages' in x:
            proceedings.append(f"pp. {x['pages']}")
        if proceedings:
            paper += ', '.join(proceedings) + '. '
        date = [str(x[field]) for field in ('month', 'year') if field in x]
        if date:
            paper += ', '.join(date) + '. '
        if 'doi' in x:
            paper += "\\url{" + x['doi'] +"}"
        clist.append(paper)
    return clist


def create_domestic(xd) -> ([str], int):
    dlist = []
    myname = "儀間 達也"
    count = 0

    for x in xd:
        author_mark(x)
        paper = ', '.join(x['author']) + '.\n\t``' + x['title'] + ".''\n\t"
        if myname == x.get('presenter'):
            count += 1
        dlist.append(paper + x.get('booktitle', ''))
    return dlist, count

# main part 

with open(out, mode='w') as wj, open(template, mode='r') as tpl:
    wj.write(tpl.read())

    with open(publication_data, mode='r') as cd:
        db = yaml.safe_load(cd)

        # Journal
        wj.write('\\section{査読付き国際論文誌論文}\n' + '\\begin{enumerate}\n')
        jlist = create_journal_list(db['journal'])
        for x in jlist:
            paper = '\t\\item ' + x
            wj.write(paper + '\n')

        wj.write('\\end{enumerate}\n\n')


        # Conference
        wj.write('\\section{査読付き国際会議論文}\n' + '*付きは発表者を表す．\n' + '\\begin{enumerate}\n')
        clist = create_conference_list(db['conference'])
        for x in clist:
            paper = '\t\\item ' + x
            wj.write(paper + '\n')
        wj.write('\\end{enumerate}\n')

        # Workshop
        wj.write('\\section{国際ワークショップ等での発表}\n' + '*付きは発表者を表す．\n''\\begin{enumerate}\n')
        clist = create_conference_list(db['workshop'])
        for x in clist:
            paper = '\t\\item ' + x
            wj.write(paper + '\n')
        wj.write('\\end{enumerate}\n')

        # # preprints
        # wjp.write("### プレプリント\n")
        # wen.write("### Preprint papers\n")
        # clist = create_preprint_papers(db['arxiv'])
        # for x in clist:
        #     paper = '1. ' + x
        #     wjp.write(paper + '\n')
        #     wen.write(paper + '\n')
        # wjp.write('{reversed="reversed"}\n')
        # wen.write('{reversed="reversed"}\n')


        wj.write("\\section{国内研究会等での発表}\n")
        dlist, count = create_domestic(db["domestic"])
        wj.write("うち，儀間発表 " + str(count) + "件\n" + '\n\n*付きは発表者を表す．\n' +'\\begin{enumerate}')
        for x in dlist:
            paper = '\t\\item ' + x
            wj.write(paper + '\n')
        wj.write('\\end{enumerate}\n')

    wj.write("\\end{document}\n")
