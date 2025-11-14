import requests
from bs4 import BeautifulSoup


def scrape_lego_product_info(item_id):
    """
    Scrape LEGO product information from Brickset.com or LEGO.com
    Returns a dict with 'name' and 'image_url' keys, or None if not found
    """
    product_info = {}
    
    # Try Brickset.com first
    try:
        url = f"https://brickset.com/sets/{item_id}-1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the set name
            name_elem = soup.find('h1', class_='set-title')
            if name_elem:
                product_info['name'] = name_elem.get_text(strip=True)
            
            # Try to find the image - try multiple selectors
            img_elem = None
            # Try mainimage class first
            img_elem = soup.find('img', class_='mainimage')
            # Try data-src attribute (lazy loaded images)
            if not img_elem:
                img_elem = soup.find('img', {'data-src': True})
            # Try any img with 'set' in the src
            if not img_elem:
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or ''
                    if 'set' in src.lower() and ('jpg' in src.lower() or 'png' in src.lower() or 'webp' in src.lower()):
                        img_elem = img
                        break
            
            if img_elem:
                img_url = img_elem.get('src') or img_elem.get('data-src') or ''
                if img_url:
                    if not img_url.startswith('http'):
                        img_url = 'https://brickset.com' + img_url
                    product_info['image_url'] = img_url
            
            if product_info.get('name') and product_info.get('image_url'):
                return product_info
    except Exception as e:
        print(f"Error scraping Brickset: {e}")
    
    # Try LEGO.com as fallback
    try:
        url = f"https://www.lego.com/en-us/product/{item_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the product name
            name_elem = soup.find('h1', {'data-test': 'product-overview-name'}) or soup.find('h1', class_='ProductOverviewstyles__Title')
            if name_elem:
                product_info['name'] = name_elem.get_text(strip=True)
            
            # Try to find the image - try multiple selectors
            img_elem = None
            # Try data-test attribute
            img_elem = soup.find('img', {'data-test': 'product-image'})
            # Try ProductImagestyles__Image class
            if not img_elem:
                img_elem = soup.find('img', class_='ProductImagestyles__Image')
            # Try any img with product in src or data attributes
            if not img_elem:
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
                    if 'product' in src.lower() or 'lego' in src.lower():
                        if 'jpg' in src.lower() or 'png' in src.lower() or 'webp' in src.lower():
                            img_elem = img
                            break
            
            if img_elem:
                img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src') or ''
                if img_url:
                    if not img_url.startswith('http'):
                        img_url = 'https://www.lego.com' + img_url
                    product_info['image_url'] = img_url
            
            if product_info.get('name') and product_info.get('image_url'):
                return product_info
    except Exception as e:
        print(f"Error scraping LEGO.com: {e}")
    
    # Return whatever we found, even if incomplete
    return product_info if product_info else None

