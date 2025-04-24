import os
from openai import AzureOpenAI
import datetime
import base64
import json
from dotenv import load_dotenv
# Playwright imports
from playwright.sync_api import sync_playwright, expect
import time

# Load environment variables
load_dotenv()

# Get estimated cost per call
estimated_cost_per_call = float(os.getenv("ESTIMATED_COST_PER_CALL", "0.0"))

# Simple logger function
def log_event(event: str):
    """Log an event to the log file."""
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {event}\n")
    # Also print to console for immediate feedback
    print(f"LOG: {event}")

# Function to show a status message on screen
def show_status_overlay(page, message):
    try:
        page.evaluate(f'''message => {{
            // Remove existing overlay if any
            const existingOverlay = document.getElementById('status-overlay');
            if (existingOverlay) {{
                existingOverlay.remove();
            }}
            
            // Create new overlay
            const overlay = document.createElement('div');
            overlay.id = 'status-overlay';
            overlay.style.position = 'fixed';
            overlay.style.top = '10px';
            overlay.style.right = '10px';
            overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            overlay.style.color = 'white';
            overlay.style.padding = '10px';
            overlay.style.borderRadius = '5px';
            overlay.style.zIndex = '9999';
            overlay.style.maxWidth = '300px';
            overlay.style.fontSize = '16px';
            overlay.textContent = message;
            
            document.body.appendChild(overlay);
        }}''', message)
    except Exception as e:
        log_event(f"WARNING: Could not show overlay: {str(e)}")

log_event("INFO: Starting computer agent with Azure OpenAI")
log_event(f"INFO: Estimated cost per call: ${estimated_cost_per_call}")

# Launch Playwright browser
log_event("INFO: Launching Playwright browser")
with sync_playwright() as playwright:
    # Launch the browser (can use 'chromium', 'firefox', or 'webkit')
    browser = playwright.chromium.launch(headless=False)  # Set headless=False to see the browser
    
    # Create a new context (like a new browser profile)
    context = browser.new_context(viewport={"width": 1024, "height": 768})
    
    # Open a new page (tab)
    page = context.new_page()
    
    try:
        # Navigate to Bing
        log_event("INFO: Navigating to Bing")
        show_status_overlay(page, "Navigating to Bing...")
        
        # Ensure navigation works by trying multiple approaches
        try:
            # Try basic navigation first
            log_event("INFO: Trying basic navigation to Bing")
            page.goto("https://www.bing.com", wait_until="domcontentloaded", timeout=60000)
            log_event("INFO: Successfully navigated to Bing")
            
            # Wait for network to be idle
            log_event("INFO: Waiting for network idle")
            page.wait_for_load_state("networkidle", timeout=30000)
            
        except Exception as e:
            log_event(f"WARNING: Issue with navigation: {str(e)}")
            try:
                # Try again with a different URL - the search page
                log_event("INFO: Trying alternative navigation to Bing search")
                page.goto("https://www.bing.com/search", wait_until="domcontentloaded", timeout=60000)
                log_event("INFO: Navigated to Bing search instead")
                
                # Wait for network to be idle
                page.wait_for_load_state("networkidle", timeout=30000)
                
            except Exception as e2:
                log_event(f"WARNING: Alternative navigation failed: {str(e2)}")
                # Try a simpler navigation as last resort
                log_event("INFO: Trying simplified navigation")
                page.goto("https://www.bing.com", timeout=90000)
                log_event("INFO: Completed basic navigation to Bing")
        
        # Let the page settle
        log_event("INFO: Letting page settle")
        time.sleep(3)
        
        # Try to ensure we have a valid page before proceeding
        try:
            # Check if we're on Bing or at least some website
            page_title = page.title()
            log_event(f"INFO: Page title: {page_title}")
            show_status_overlay(page, f"Loaded page: {page_title}")
        except Exception as e:
            log_event(f"WARNING: Could not get page title: {str(e)}")
        
        # Help the agent by pre-filling the search box if we can find it
        log_event("INFO: Starting search box detection and prefilling")
        
        # First, try to detect all potential search boxes and log their presence
        selectors_to_check = [
            'input[name="q"]',
            'input[type="search"]',
            'input[type="text"]',
            'input[aria-label*="search"]',
            'input[aria-label*="Search"]',
            '#sb_form_q',  # Specific Bing search box ID
            '.b_searchbox',  # Bing search box class
            '[name="q"]',  # Common search param
            '#search_form',  # Bing search form
            'form input'  # Any input in a form
        ]
        
        search_button_selectors = [
            '#search_icon',  # Bing search icon
            'button[type="submit"]',  # Generic submit button
            'input[type="submit"]',  # Submit input
            '#sb_form_go',  # Bing search button
            '.search-button',  # Generic search button class
            '[aria-label*="Search"]',  # Anything with search in aria-label
            'svg[aria-label*="Search"]',  # SVG icon with search in aria-label
            'button.b_searchboxSubmit'  # Bing specific submit button
        ]
        
        log_event(f"INFO: Checking for {len(selectors_to_check)} different selectors")
        
        # First, just detect which selectors are present on the page
        for selector in selectors_to_check:
            try:
                count = page.eval_on_selector_all(selector, 'elements => elements.length')
                log_event(f"SELECTOR CHECK: '{selector}' - Found: {count} elements")
                
                # Get more info about the elements
                if count > 0:
                    element_info = page.eval_on_selector_all(selector, '''elements => {
                        return elements.map(el => ({
                            visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                            tag: el.tagName,
                            id: el.id,
                            type: el.getAttribute('type'),
                            name: el.getAttribute('name'),
                            value: el.value
                        }));
                    }''')
                    log_event(f"ELEMENT INFO for '{selector}': {element_info}")
            except Exception as e:
                log_event(f"WARNING: Error checking selector '{selector}': {str(e)}")
        
        # Now check for search buttons
        log_event(f"INFO: Checking for {len(search_button_selectors)} different search button selectors")
        search_button_selector = None
        
        for selector in search_button_selectors:
            try:
                is_visible = page.is_visible(selector)
                log_event(f"BUTTON CHECK: '{selector}' - Visible: {is_visible}")
                if is_visible:
                    search_button_selector = selector
                    log_event(f"INFO: Found visible search button with selector: '{selector}'")
                    break
            except Exception as e:
                log_event(f"WARNING: Error checking button selector '{selector}': {str(e)}")
        
        # Take a screenshot to help debug
        log_event("INFO: Taking screenshot of page before search box interaction")
        page.screenshot(path="before_search_prefill.png")
        
        # Now try to actually find and interact with the search box
        search_box = None
        search_found = False
        used_selector = None
        
        # Try a more direct approach - use the page.fill method which is more robust
        for selector in selectors_to_check:
            try:
                log_event(f"INFO: Trying to fill search box with selector: '{selector}'")
                # First check if element exists and is visible
                is_visible = page.is_visible(selector)
                log_event(f"INFO: Selector '{selector}' is visible: {is_visible}")
                
                if is_visible:
                    # Try to click and fill the search box
                    page.click(selector, timeout=5000)
                    log_event(f"INFO: Successfully clicked on '{selector}'")
                    
                    # Clear the field first
                    page.fill(selector, "")
                    log_event(f"INFO: Cleared text field")
                    
                    # Type the search text with delay to ensure it's visible
                    page.fill(selector, "AI news")
                    log_event(f"INFO: Successfully filled '{selector}' with 'AI news'")
                    
                    # Take a screenshot to verify
                    page.screenshot(path=f"filled_search_with_{selector.replace('[', '_').replace(']', '_').replace('*', '_')}.png")
                    
                    search_found = True
                    used_selector = selector
                    
                    # Success - break the loop
                    break
            except Exception as e:
                log_event(f"WARNING: Failed to interact with '{selector}': {str(e)}")
        
        # If we found the search box, highlight it
        if search_found:
            log_event(f"INFO: Successfully found and filled search box using selector: '{used_selector}'")
            show_status_overlay(page, f"Found and filled search box with 'AI news' using {used_selector}")
            
            try:
                # Highlight the search box for visibility
                page.evaluate(f'''() => {{
                    const searchBox = document.querySelector('{used_selector}');
                    if (searchBox) {{
                        searchBox.style.border = '3px solid red';
                        searchBox.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.7)';
                        searchBox.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                }}''')
                log_event("INFO: Search box highlighted with red border")
            except Exception as e:
                log_event(f"WARNING: Could not highlight search box: {str(e)}")
            
            # Take another screenshot with the highlighted search box
            page.screenshot(path="prefilled_search_highlighted.png")
            
            # Now try to execute the search by pressing Enter or clicking the search button
            log_event("INFO: Attempting to execute search...")
            search_executed = False
            
            # Method 1: Try pressing Enter on the search box
            try:
                log_event("INFO: Trying to press Enter on the search box")
                page.press(used_selector, "Enter")
                log_event("INFO: Successfully pressed Enter on search box")
                search_executed = True
                time.sleep(2)  # Wait for search results to load
                page.screenshot(path="after_enter_press.png")
            except Exception as e:
                log_event(f"WARNING: Failed to press Enter: {str(e)}")
                
                # Method 2: Try clicking a search button if available
                if search_button_selector:
                    try:
                        log_event(f"INFO: Trying to click search button with selector: '{search_button_selector}'")
                        page.click(search_button_selector)
                        log_event("INFO: Successfully clicked search button")
                        search_executed = True
                        time.sleep(2)  # Wait for search results to load
                        page.screenshot(path="after_button_click.png")
                    except Exception as e:
                        log_event(f"WARNING: Failed to click search button: {str(e)}")
                
                # Method 3: Try using JavaScript to submit the form
                if not search_executed:
                    try:
                        log_event("INFO: Trying to submit form via JavaScript")
                        page.evaluate('''() => {
                            const searchBox = document.querySelector('input[type="search"], input[type="text"], #sb_form_q, [name="q"]');
                            if (searchBox) {
                                const form = searchBox.closest('form');
                                if (form) {
                                    form.submit();
                                    return true;
                                }
                            }
                            return false;
                        }''')
                        log_event("INFO: Attempted form submission via JavaScript")
                        time.sleep(2)  # Wait for search results to load
                        page.screenshot(path="after_js_submit.png")
                        search_executed = True
                    except Exception as e:
                        log_event(f"WARNING: Failed to submit form via JavaScript: {str(e)}")
            
            if search_executed:
                log_event("INFO: Search execution attempt completed")
                # Wait for the results page to load
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                    log_event("INFO: Search results page loaded")
                except Exception as e:
                    log_event(f"WARNING: Network idle wait issue: {str(e)}")
            
        else:
            log_event("WARNING: Could not find or interact with any search box")
            show_status_overlay(page, "Search box not found for prefilling")
            
            # Take a screenshot of the page in its current state
            page.screenshot(path="search_box_not_found.png")
            
            # As a last resort, try using JavaScript to find and fill a search input
            try:
                page.evaluate('''() => {
                    // Try to find ANY input that could be a search box
                    const inputs = Array.from(document.querySelectorAll('input'));
                    const searchBox = inputs.find(input => 
                        input.type === 'text' || 
                        input.type === 'search' || 
                        input.name === 'q' || 
                        input.placeholder?.toLowerCase().includes('search') ||
                        input.ariaLabel?.toLowerCase().includes('search')
                    );
                    
                    if (searchBox) {
                        searchBox.value = 'AI news';
                        searchBox.style.border = '3px solid red';
                        searchBox.scrollIntoView({behavior: 'smooth', block: 'center'});
                        console.log('Found and filled search box via JavaScript');
                        
                        // Try to submit the form
                        const form = searchBox.closest('form');
                        if (form) {
                            setTimeout(() => {
                                form.submit();
                            }, 500);
                        }
                        
                        return true;
                    }
                    return false;
                }''')
                log_event("INFO: Attempted JavaScript-based search box detection, filling and submission")
                time.sleep(2)  # Wait for possible form submission
                page.screenshot(path="javascript_search_attempt.png")
            except Exception as e:
                log_event(f"WARNING: JavaScript search attempt failed: {str(e)}")
        
        # Take a screenshot of the initial state
        log_event("INFO: Taking screenshot of initial state")
        page.screenshot(path="initial_state.png")
        
        # Initialize AzureOpenAI client
        log_event("INFO: Initializing Azure OpenAI client")
        client = AzureOpenAI()
        
        # Variables for the loop
        task_completed = False
        max_iterations = 3  # Reduced from 5 to 3 iterations
        iteration = 0
        total_cost = 0
        
        # Continue until the task is completed or max iterations reached
        while not task_completed and iteration < max_iterations:
            iteration += 1
            log_event(f"INFO: Starting iteration {iteration}/{max_iterations}")
            show_status_overlay(page, f"Starting iteration {iteration}/{max_iterations}...")
            time.sleep(1)  # Pause to let the user see the message
            
            # Very specific and clear instructions for the agent
            if iteration == 1:
                # First iteration: If search wasn't executed automatically, help the agent complete it
                current_prompt = """
                Look at the browser. It should show a search box with 'AI news' already typed in.
                Steps:
                1. Press Enter key or click the search button next to the search box
                2. Wait for search results to load
                That's all for this step.
                """
            else:
                # Later iterations: focus on clicking a news article
                current_prompt = """
                Look at the search results for 'AI news'. 
                Steps:
                1. Find and click on any news article about AI or artificial intelligence
                2. If you already clicked an article, scroll down to read more of it
                """
            
            input_messages = [
                {
                    "role": "user",
                    "content": current_prompt
                }
            ]
            
            # Tools
            tools = [{
                    "type": "computer_use_preview",
                    "display_width" : 1024,
                    "display_height" : 768,
                    "environment": "browser"      
            }]
            
            log_event(f"INFO: Sending request to computer-use-preview model (iteration {iteration})")
            show_status_overlay(page, f"Iteration {iteration}/{max_iterations}: Sending request to Computer Use agent...")
            time.sleep(2)  # Pause to let the user see the message
            
            try:
                # Make the API call
                show_status_overlay(page, f"Iteration {iteration}/{max_iterations}: Agent is analyzing and controlling the browser...")
                response = client.responses.create(
                    model = 'computer-use-preview',
                    input = input_messages,
                    tools = tools,
                    reasoning = { 
                        "generate_summary" : "concise"
                    },
                    truncation = "auto" 
                )
                
                # Increment call count and calculate cost
                total_cost += estimated_cost_per_call
                
                log_event(f"INFO: Response received successfully (iteration {iteration})")
                log_event(f"INFO: Output: {response.output}")
                print(f"Iteration {iteration} response:")
                print(response.output)
                
                show_status_overlay(page, f"Iteration {iteration}/{max_iterations}: Agent response received! Processing...")
                time.sleep(2)  # Pause to let the user see the message
                
                # Take screenshot after agent actions
                log_event(f"INFO: Taking screenshot after iteration {iteration}")
                page.screenshot(path=f"state_after_iteration_{iteration}.png")
                
                # Check if the task is completed
                # This is a simple check - you might want to improve this logic
                response_text = str(response.output).lower()
                if iteration >= 2 and ("article" in response_text or "clicked" in response_text or "news" in response_text):
                    task_completed = True
                    log_event("INFO: Task completed successfully - AI news article found")
                    show_status_overlay(page, "SUCCESS! AI news article opened!")
                elif iteration == max_iterations:
                    log_event("INFO: Maximum iterations reached without completion")
                    show_status_overlay(page, "Maximum iterations reached. Task may not be complete.")
                else:
                    show_status_overlay(page, f"Iteration {iteration} complete. Continuing search...")
                
                # Check if page URL contains indicators of success
                try:
                    current_url = page.url
                    log_event(f"INFO: Current URL: {current_url}")
                    if "news" in current_url.lower() or "article" in current_url.lower():
                        task_completed = True
                        log_event("INFO: URL indicates successful navigation to news article")
                        show_status_overlay(page, "SUCCESS! News article page detected!")
                except:
                    pass
                
                # Short pause to allow the page to update completely and for user to observe
                time.sleep(3)
                
            except Exception as e:
                log_event(f"ERROR: An error occurred in iteration {iteration}: {str(e)}")
                show_status_overlay(page, f"ERROR in iteration {iteration}: {str(e)[:50]}...")
                # Take error screenshot
                try:
                    page.screenshot(path=f"error_state_iteration_{iteration}.png")
                except:
                    pass
                # Don't break the loop, try again with the next iteration if possible
                time.sleep(3)  # Let user see the error message
        
        # Final summary
        log_event(f"INFO: Process completed after {iteration} iterations")
        log_event(f"INFO: Total estimated cost: ${total_cost:.4f}")
        log_event(f"INFO: Task completed successfully: {task_completed}")
        
        # Take a final screenshot
        log_event("INFO: Taking final screenshot")
        page.screenshot(path="final_state.png")
        
        show_status_overlay(page, f"Process completed! Iterations: {iteration}, Cost: ${total_cost:.4f}, Success: {task_completed}")
        
        # Longer pause to see the final state (10 seconds)
        time.sleep(10)
        
    except Exception as e:
        log_event(f"ERROR: A browser error occurred: {str(e)}")
        # Take error screenshot
        try:
            page.screenshot(path="error_state.png")
            show_status_overlay(page, f"ERROR: {str(e)[:100]}...")
            time.sleep(5)  # Let user see the error
        except:
            pass
        raise
    
    finally:
        # Close the browser
        log_event("INFO: Closing browser")
        browser.close()


