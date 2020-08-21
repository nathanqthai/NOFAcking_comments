# NOFAcking_comments
a tool to scrape comments from NOFAs on beta.regulations.gov w/o an api key

## a rant
im going to preface this by saying that i could be completely wrong and just misunderstanding the api... but... idk

so... the [actual api](https://open.gsa.gov/api/regulationsgov) is _COMPLETELY_ busted as of 20200820.

if you attempt to hit any of the endpoints with a `{documentId}` in the path you will get back a `400` saying there is no filter named `docId`.

because of that, we have gone out and fetched the api calls used by the site itself. this happens to have its own pitfalls.

the page sizes are capped to 25 elements per page and a max of 20 pages. thats it. if there are more than 500 results you can gfy.

to get around that we basically just scrape as many pages as we can per day from the day comments are open. it seems unlikely there would be more than 500 comments in a day but if there are you can gfy. this hack cant get around that limitation because the date granularity is limited to days.
