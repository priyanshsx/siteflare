Insights we're gathering: 



Generic
1. Google PageSpeed Insights: LCP, FID/INP, CLS, TTFB, and an overall performance score. 
2. Page Load Time, total page size, number of requests - extractable via requests/httpx
3. Image optimization check 

SEO 
1. Title tag presence/length, meta description presence/length
2. Heading structure 
3. Missing alt text on images 
4. Canonical tag presence 
5. robotx.txt presence and content 
6. XML sitemap presence 
8. Word count/thin content detection per page 

Security 
1. HTTPS enforcement 
2. SSL certificate 
3. Mixed content warnings 
4. HTTP security headers: content security policy, X-frame-options, strict-transport-security 
5. HTTP/2 or HTTP/3 support 

UX 
1. Viewport meta tag presence 
2. Tap target sizing/text size 

Marketing Stack
1. Detect presence of Google Analytics (GA4/UA), Google Tag Manager, Meta Pixel, LinkedIn Insight Tag, TikTok Pixel, HubSpot, Intercom, etc. — done by pattern-matching known script URLs/IDs in the page source. This is exactly how tools like BuiltWith/Wappalyzer work under the hood; Wappalyzer's detection logic is actually open-source (their fingerprint database), so you can build your own lightweight version referencing publicly known script signatures — just don't call their paid API.
2. CMS detection (WordPress, Shopify, Webflow, Squarespace) via known meta generator tags, file paths (/wp-content/), or common asset patterns.

Content Age 
1. Blog/news section last-updated date 
2. Sitemap lastmod timestamps, if present in sitemap.xml 
3. Copyright year in footer 

Socials 
1. Open Graph tags presence 
2. Twitter Card tags presence 
3. Social profile links detection
4. Favicon presence 

Accessibility 
1. Missing alt text  
2. Missing form labels

DNS 
1. dns records 
2. DNSSEC status 

