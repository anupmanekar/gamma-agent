from crawlee.crawlers import PlaywrightCrawler
import asyncio

async def handle_request(context):
    page = context.page
    await page.goto(context.request.url)
    #url = context.request.url
    #print(f"Processing: {url}")
    await page.pause()  # Pause to visually inspect the browser
    # Evaluate script in the page context to get all elements' tag names and attributes
    elements = await page.evaluate(
        """() => {
            const allElements = Array.from(document.querySelectorAll('*'));
            return allElements.map(el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return {
                    tag: el.tagName,
                    attributes: attrs,
                    text: el.innerText
                };
            });
        }"""
    )

    # Output or save the scraped data
    for el in elements:
        print(el)

    # Optionally store data in Crawlee dataset
    #await Dataset.push_data(elements)


async def main():
    crawler = PlaywrightCrawler(
        max_requests_per_crawl=1,  # Process only one page here
        request_handler=handle_request,
        browser_launch_options={"headless": False},
    )
    await crawler.run(["https://manekaranupwork-1759512410216.atlassian.net/jira/software/projects/SCRUM/boards/1"])

# To run this, use an async event loop like in an async main script
asyncio.run(main())
