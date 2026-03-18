import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


def _normalize_image_url(url, base_url=''):
    """Normalize image URL to absolute URL"""
    if not url:
        return None
    if url.startswith('http'):
        return url
    if base_url and not url.startswith('/'):
        url = '/' + url
    return base_url + url if base_url else url


def _find_images_by_pattern(soup, item_id, base_url='', html_content=''):
    """
    Find images matching priority patterns (case-insensitive):
    1. {item_id}_box1
    2. {item_id}_box5
    3. {item_id}_boxprod_.
    4. {item_id}.
    5. {item_id}_web
    6. All images starting with {item_id}
    
    Returns tuple: (selected_image_url, all_matching_images_list)
    """
    all_images = []
    selected_image = None
    found_urls = set()  # Use set to avoid duplicates
    
    # Normalize item_id to lowercase for case-insensitive matching
    item_id_lower = item_id.lower()
    
    # First, search img tags
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-srcset') or ''
        if not src:
            continue
        
        # Normalize the URL
        normalized_url = _normalize_image_url(src, base_url)
        if not normalized_url:
            continue
        
        # Extract filename from URL (handle query parameters)
        parsed = urlparse(normalized_url)
        filename = parsed.path.split('/')[-1]
        
        # Check if image starts with item_id (case-insensitive)
        if filename.lower().startswith(item_id_lower):
            found_urls.add(normalized_url)
    
    # Also search the raw HTML content for image URLs (they might be in JSON/data attributes)
    if html_content:
        # Pattern to find full URLs containing the item_id with image extensions (case-insensitive)
        url_pattern = rf'(https?://[^\s\"\'<>]*?/{re.escape(item_id)}[^\s\"\'<>]*?\.(?:jpg|jpeg|png|webp))'
        url_matches = re.findall(url_pattern, html_content, re.IGNORECASE)
        for url_match in url_matches:
            # Clean up the URL (remove query parameters for matching, but keep original)
            parsed = urlparse(url_match)
            filename = parsed.path.split('/')[-1]
            if filename.lower().startswith(item_id_lower):
                found_urls.add(url_match)
    
    # Process found URLs and prioritize them
    # We need to check all URLs first, then select the highest priority one
    priority_matches = {
        1: None,  # box1
        2: None,  # box5
        3: None,  # boxprod
        4: None,  # item_id.
        5: None,  # web
    }
    
    for normalized_url in found_urls:
        # Extract filename from URL
        parsed = urlparse(normalized_url)
        filename = parsed.path.split('/')[-1]
        # Remove query parameters from filename for pattern matching
        filename_base = filename.split('?')[0]
        filename_base_lower = filename_base.lower()
        
        all_images.append(normalized_url)
        
        # Priority 1: {item_id}_box1 (case-insensitive)
        if filename_base_lower.startswith(f"{item_id_lower}_box1") and priority_matches[1] is None:
            priority_matches[1] = normalized_url
        
        # Priority 2: {item_id}_box5 (case-insensitive)
        elif filename_base_lower.startswith(f"{item_id_lower}_box5") and priority_matches[2] is None:
            priority_matches[2] = normalized_url
        
        # Priority 3: {item_id}_boxprod_. (case-insensitive)
        elif filename_base_lower.startswith(f"{item_id_lower}_boxprod_") and priority_matches[3] is None:
            priority_matches[3] = normalized_url
        
        # Priority 4: {item_id}. (but not box1, box5, boxprod or web) (case-insensitive)
        elif filename_base_lower.startswith(f"{item_id_lower}.") and not filename_base_lower.startswith(f"{item_id_lower}_") and priority_matches[4] is None:
            priority_matches[4] = normalized_url
        
        # Priority 5: {item_id}_web (case-insensitive)
        elif filename_base_lower.startswith(f"{item_id_lower}_web") and priority_matches[5] is None:
            priority_matches[5] = normalized_url
    
    # Select the highest priority match found
    for priority in sorted(priority_matches.keys()):
        if priority_matches[priority] is not None:
            selected_image = priority_matches[priority]
            break
    
    # If no priority match found but we have matching images, use first one
    if not selected_image and all_images:
        selected_image = all_images[0]
    
    return selected_image, all_images


def scrape_lego_product_info(item_id):
    """
    Scrape LEGO product information from Brickset.com or LEGO.com
    Returns a dict with 'name', 'image_url', and 'image_options' keys, or None if not found
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
            html_content = response.text

            # Try to find the set name (class was removed from h1 in 2025)
            name_elem = soup.find('h1', class_='set-title') or soup.find('h1')
            if name_elem:
                name = name_elem.get_text(strip=True)
                # Brickset h1 now includes the item_id prefix, e.g. "10317 Land Rover..."
                if name.startswith(f"{item_id} "):
                    name = name[len(item_id):].strip()
                product_info['name'] = name
            
            # Find images using priority pattern matching
            selected_image, all_images = _find_images_by_pattern(soup, item_id, 'https://brickset.com', html_content)
            
            if selected_image:
                product_info['image_url'] = selected_image
                # Include all matching images as options if multiple found
                if len(all_images) > 1:
                    product_info['image_options'] = all_images
            else:
                # Fallback to old logic if no pattern-matched images found
                img_elem = None
                img_elem = soup.find('img', class_='mainimage')
                if not img_elem:
                    img_elem = soup.find('img', {'data-src': True})
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
            html_content = response.text
            
            # Try to find the product name
            name_elem = soup.find('h1', {'data-test': 'product-overview-name'}) or soup.find('h1', class_='ProductOverviewstyles__Title')
            if name_elem:
                product_info['name'] = name_elem.get_text(strip=True)
            
            # Find images using priority pattern matching
            selected_image, all_images = _find_images_by_pattern(soup, item_id, 'https://www.lego.com', html_content)
            
            if selected_image:
                product_info['image_url'] = selected_image
                # Include all matching images as options if multiple found
                if len(all_images) > 1:
                    product_info['image_options'] = all_images
            else:
                # Fallback to old logic if no pattern-matched images found
                img_elem = None
                img_elem = soup.find('img', {'data-test': 'product-image'})
                if not img_elem:
                    img_elem = soup.find('img', class_='ProductImagestyles__Image')
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

