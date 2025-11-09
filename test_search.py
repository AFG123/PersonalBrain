from vector import search

q = 'Middleware Technology Unit 1'
results = search(q, k=6)
print('Found', len(results), 'results')
for i, r in enumerate(results):
    print(i+1, r.metadata.get('source'), r.page_content[:200].replace('\n',' '))
