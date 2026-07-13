# Junk page detection

Policy version: 1.0

The Gatekeeper must reject records that are clearly not procurement
opportunities. This includes pages whose primary purpose is any of the
following:

- login, sign-in, account, password-reset, or registration;
- advertising, sponsorship, or promotional content;
- training courses, events, webinars, or certifications;
- news articles, press releases, or blog posts that do not publish an active
  procurement notice;
- career postings, internships, recruitment, or employment applications;
- procurement guidance, help pages, policy documents, or generic portal
  landing pages; or
- site navigation, category pages, cookie notices, and other website chrome.

## Evidence standard

Use the title, URL, cleaned description, and source context together. A single
word is not always enough to reject a page: for example, a tender may mention
training as part of its scope. Reject only when the page's primary purpose is
clearly junk or non-procurement content.

The decision reason must identify the evidence, for example: `Registration
landing page; no procurement scope or buyer found.`
