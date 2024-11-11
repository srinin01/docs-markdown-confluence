from atlassian import Confluence

# Initialize Confluence client
confluence = Confluence(
    url='https://nallurisrini01-1729828114293.atlassian.net',
    username='nallurisrini01@gmail.com',
    password='ATATT3xFfGF0Yd9tL0PEM3jJHw86yeGf6jaGj39in75SwFU5kHm3Y_mo2JCGCaRDCGn6OWG9B2JteyHVqDAfEDz9fF3cr2f3eXG7739Y_YPkp73KR3axIHvP5_WxtIXsO4CEV0NLp3u4goGqqHenxj3AOUeYsE7PuYYxEV_VyMQ3AZdybJivCYU=C7EAC801'
)

def check_space_exists(space_key):
    try:
        confluence.get_space(space_key)
        print(confluence.page_exists(space_key, "Hello123"))
        return True
    except Exception as e:
        if "does not exist" in str(e):
            return False
        else:
            raise e

# Example usage:
space_key = 'mymarkdown'
if check_space_exists(space_key):
    print(f'Space {space_key} exists.')
else:
    print(f'Space {space_key} does not exist.')