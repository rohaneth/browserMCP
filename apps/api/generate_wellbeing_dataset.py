import json
import random
from datetime import datetime, timedelta

events = []

# 1. Recovery / Productive Morning (Pomodoro + Notion + GitHub) (~10 events)
t = datetime(2026, 8, 20, 9, 30, 0)
morning_events = [
    ("https://pomofocus.io/", "Pomofocus - Pomodoro Timer Online", "navigation", None),
    ("https://www.notion.so/my-workspace/Daily-Engineering-Plan-2026", "Daily Engineering Plan - Notion", "navigation", None),
    ("https://github.com/rohan-dev/enterprise-spring-service", "rohan-dev/enterprise-spring-service: Production backend repo", "navigation", None),
    ("https://github.com/rohan-dev/enterprise-spring-service/pull/14", "feat: add distributed cache layer by rohan-dev · Pull Request #14", "navigation", None),
    ("https://docs.google.com/document/d/1aB3c4D5e6F7g8H9/edit", "Sprint 34 Architecture Design Notes - Google Docs", "navigation", None),
    ("https://docs.google.com/document/d/1aB3c4D5e6F7g8H9/edit", "Sprint 34 Architecture Design Notes - Google Docs", "input", "Added notes on redis fallback"),
    ("https://github.com/rohan-dev/enterprise-spring-service/commits/main", "Commits · rohan-dev/enterprise-spring-service", "navigation", None),
    ("https://pomofocus.io/", "Pomofocus - Break Finished", "navigation", None),
    ("https://www.notion.so/my-workspace/Tasks-Backlog", "Engineering Backlog & Sprints - Notion", "navigation", None),
    ("https://github.com/rohan-dev/enterprise-spring-service/actions", "Actions · rohan-dev/enterprise-spring-service · CI/CD Passed", "navigation", None)
]

for url, title, ev, inp in morning_events:
    t += timedelta(seconds=random.randint(120, 300))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp: e["input"] = inp
    events.append(e)

# 2. Deep Work Java Session (~25 events, sustained focus, 20-40 min dwell)
t = datetime(2026, 8, 20, 11, 0, 0)
java_topics = [
    ("https://www.google.com/search?q=spring+boot+3+hibernate+6+batch+insert+performance", "spring boot 3 hibernate 6 batch insert performance - Google Search", "search_submitted", "spring boot 3 hibernate 6 batch insert performance"),
    ("https://docs.spring.io/spring-boot/docs/current/reference/html/data.html#data.sql.jpa-and-spring-data", "Spring Boot Reference Documentation - Data Access with JPA", "navigation", None),
    ("https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html", "Spring Data JPA - Reference Documentation: Query Methods", "navigation", None),
    ("https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#batch", "Hibernate ORM 6.4 User Guide - Batch Processing", "navigation", None),
    ("https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#identifiers-generators", "Hibernate ORM 6.4 - Identifier Generators & SequenceAllocation", "navigation", None),
    ("https://stackoverflow.com/questions/56884632/spring-data-jpa-saveall-is-very-slow-with-identity-generation", "java - Spring Data JPA saveAll() is very slow with IDENTITY generation - Stack Overflow", "navigation", None),
    ("https://stackoverflow.com/questions/56884632/spring-data-jpa-saveall-is-very-slow-with-identity-generation", "java - Spring Data JPA saveAll() is very slow with IDENTITY generation - Stack Overflow", "input", "jdbc.batch_size=50"),
    ("https://vladmihalcea.com/how-to-batch-insert-and-update-statements-with-hibernate/", "The best way to batch INSERT statements with Hibernate - Vlad Mihalcea", "navigation", None),
    ("https://vladmihalcea.com/hibernate-identity-sequence-generator/", "Why you should never use the IDENTITY generator with Hibernate - Vlad Mihalcea", "navigation", None),
    ("https://www.google.com/search?q=spring+security+6+jwt+stateless+authentication+filter+chain", "spring security 6 jwt stateless authentication filter chain - Google Search", "search_submitted", "spring security 6 jwt stateless authentication filter chain"),
    ("https://docs.spring.io/spring-security/reference/servlet/authentication/architecture.html", "Authentication Architecture :: Spring Security Reference", "navigation", None),
    ("https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html", "OAuth 2.0 Resource Server JWT :: Spring Security Reference", "navigation", None),
    ("https://github.com/spring-projects/spring-security-samples/tree/main/servlet/spring-boot/java/jwt", "spring-security-samples/jwt at main · spring-projects/spring-security-samples", "navigation", None),
    ("https://stackoverflow.com/questions/74683204/spring-security-6-custom-jwt-filter-order-in-securityfilterchain", "java - Spring Security 6 custom JWT filter order in SecurityFilterChain - Stack Overflow", "navigation", None),
    ("https://www.google.com/search?q=spring+cloud+gateway+rate+limiter+redis+token+bucket", "spring cloud gateway rate limiter redis token bucket - Google Search", "search_submitted", "spring cloud gateway rate limiter redis token bucket"),
    ("https://docs.spring.io/spring-cloud-gateway/reference/spring-cloud-gateway/gatewayfilter-factories/requestratelimiter-factory.html", "RequestRateLimiter GatewayFilter Factory :: Spring Cloud Gateway", "navigation", None),
    ("https://github.com/spring-cloud/spring-cloud-gateway/blob/main/spring-cloud-gateway-server/src/main/java/org/springframework/cloud/gateway/filter/ratelimit/RedisRateLimiter.java", "RedisRateLimiter.java · spring-cloud/spring-cloud-gateway", "navigation", None),
    ("https://stackoverflow.com/questions/59146123/how-to-configure-key-resolver-for-redisratelimiter-in-spring-cloud-gateway", "How to configure Key Resolver for RedisRateLimiter in Spring Cloud Gateway - Stack Overflow", "navigation", None),
    ("https://www.google.com/search?q=resilience4j+circuitbreaker+spring+boot+3+configuration", "resilience4j circuitbreaker spring boot 3 configuration - Google Search", "search_submitted", "resilience4j circuitbreaker spring boot 3 configuration"),
    ("https://resilience4j.readme.io/docs/circuitbreaker", "CircuitBreaker - Resilience4j Documentation", "navigation", None),
    ("https://resilience4j.readme.io/docs/getting-started-3", "Getting started with Spring Boot 3 - Resilience4j", "navigation", None),
    ("https://github.com/resilience4j/resilience4j-spring-boot3-demo", "resilience4j/resilience4j-spring-boot3-demo: Resilience4j Spring Boot 3 Demo Application", "navigation", None),
    ("https://stackoverflow.com/questions/75102839/resilience4j-circuitbreaker-not-opening-in-spring-boot-3", "Resilience4j CircuitBreaker not opening in Spring Boot 3 - Stack Overflow", "navigation", None),
    ("https://docs.docker.com/compose/compose-file/05-services/", "Compose file reference - Services top-level element | Docker Docs", "navigation", None),
    ("https://github.com/rohan-dev/enterprise-spring-service/pull/15", "feat: implement resilience4j circuitbreaker & redis rate limiter · Pull Request #15", "navigation", None)
]

for url, title, ev, inp in java_topics:
    t += timedelta(seconds=random.randint(60, 180))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp:
        if ev == "search_submitted": e["query"] = inp
        else: e["input"] = inp
    events.append(e)

# 3. Instagram Doomscroll Session (~60 events, 2-8s gaps, fitness, motivation, memes, reels)
t = datetime(2026, 8, 20, 14, 15, 0)
reel_ids = [
    ("C9xL1kOpA12", "Reels • Fitness motivation daily workout 5am routine"),
    ("C9xL2mQpB34", "Reels • High protein meal prep under 100 rupees"),
    ("C9xL3nRqC56", "Reels • Why your posture is ruining your jawline"),
    ("C9xL4oSrD78", "Reels • 3 stoic habits that will change your life"),
    ("C9xL5pTsE90", "Reels • Relationship red flags you should never ignore"),
    ("C9xL6qUtF11", "Reels • POV: introverts trying to survive wedding parties"),
    ("C9xL7rVuG22", "Reels • Relatable programmer memes when bug fixed in prod"),
    ("C9xL8sWvH33", "Reels • How dopamine detox fixed my ruined brain in 7 days"),
    ("C9xL9tXwI44", "Reels • Brutal reality of corporate 9 to 5 software jobs"),
    ("C9xM0uYxJ55", "Reels • Top 5 travel destinations in Himachal for solo trip"),
    ("C9xM1vZyK66", "Reels • Gym rat funny gym fails and gym bro moments"),
    ("C9xM2wAzL77", "Reels • What text messages mean when she takes 4 hours to reply"),
    ("C9xM3xBzM88", "Reels • Japanese technique to overcome laziness instantly"),
    ("C9xM4yCzN99", "Reels • Street food vendors making butter loaded sandwich"),
    ("C9xM5zDzO10", "Reels • Modern dating expectation vs reality"),
    ("C9xM6aEzP21", "Reels • Coding humor: backend vs frontend developer daily fight"),
    ("C9xM7bFzQ32", "Reels • Best budget perfumes for college guys under 500"),
    ("C9xM8cGzR43", "Reels • Uncomfortable truths about human psychology"),
    ("C9xM9dHzS54", "Reels • Cute dog doing tricks video"),
    ("C9xN0eIzT65", "Reels • Cat funny jumps and fails compilation"),
    ("C9xN1fJzU76", "Reels • Why smart people struggle to make close friends"),
    ("C9xN2gKzV87", "Reels • 5 signs someone has a secret crush on you"),
    ("C9xN3hLzW98", "Reels • Insane calisthenics planche progression in 1 year"),
    ("C9xN4iMzX09", "Reels • Best aesthetic cafes in Bangalore for working remote"),
    ("C9xN5jNzY10", "Reels • Real reason you scroll phone for 2 hours in bed"),
    ("C9xN6kOzZ21", "Reels • Standup comedy crowd work punchline clip"),
    ("C9xN7lPzA32", "Reels • Mindset shift: stop comparing your chapter 1 to chapter 20"),
    ("C9xN8mQzB43", "Reels • What to say when conversation becomes awkwardly silent"),
    ("C9xN9nRzC54", "Reels • Quick 15 minute shoulder and chest workout"),
    ("C9xO0oSzD65", "Reels • How to dress minimalist without spending money"),
    ("C9xO1pTzE76", "Reels • Indian parents reaction to IT salaries meme"),
    ("C9xO2qUzF87", "Reels • Best podcast clips on loneliness in modern 20s"),
    ("C9xO3rVzG98", "Reels • When you realize tomorrow is Monday again"),
    ("C9xO4sWzH09", "Reels • 4 cold approach conversation starters that work"),
    ("C9xO5tXzI10", "Reels • High protein vegetarian soya chunks recipe"),
    ("C9xO6uYzJ21", "Reels • Coding interview nightmare question reaction"),
    ("C9xO7vZyK32", "Reels • Travel drone shots of Spiti Valley India"),
    ("C9xO8wAzL43", "Reels • Why overthinking kills your natural confidence"),
    ("C9xO9xBzM54", "Reels • Best wireless earbuds tested for bass"),
    ("C9xP0yCzN65", "Reels • Unhinged office chat memes"),
    ("C9xP1zDzO76", "Reels • 3 morning habits for high testosterone and energy"),
    ("C9xP2aEzP87", "Reels • Psychology trick to know if someone is lying"),
    ("C9xP3bFzQ98", "Reels • Best street fashion tips for lean guys"),
    ("C9xP4cGzR09", "Reels • Funny anime logic clips"),
    ("C9xP5dHzS10", "Reels • Why living alone makes you peaceful but detached"),
    ("C9xP6eIzT21", "Reels • Hard workout motivation: no one is coming to save you"),
    ("C9xP7fJzU32", "Reels • Dating standards in 2026 discussion"),
    ("C9xP8gKzV43", "Reels • Quick 5 minute breakfast toast idea"),
    ("C9xP9hLzW54", "Reels • How to stop doomscrolling short form videos"),
    ("C9xQ0iMzX65", "Reels • Funny roommate struggles clip"),
    ("C9xQ1jNzY76", "Reels • 3 books every 20 year old must read"),
    ("C9xQ2kOzZ87", "Reels • Gym progression: 60kg bench to 120kg bench"),
    ("C9xQ3lPzA98", "Reels • When manager asks for quick 5 min call on Friday evening"),
    ("C9xQ4mQzB09", "Reels • Signs of burnout you are currently ignoring"),
    ("C9xQ5nRzC10", "Reels • Best scenic train journeys in India"),
    ("C9xQ6oSzD21", "Reels • Relationship expectations vs communication reality"),
    ("C9xQ7pTzE32", "Reels • How caffeine affects deep REM sleep quality"),
    ("C9xQ8qUzF43", "Reels • Tech layoffs update and market discussion 2026"),
    ("C9xQ9rVzG54", "Reels • Clean desk setup aesthetic for coding"),
    ("C9xR0sWzH65", "Reels • Why you feel lonely even around many people")
]

for rid, rtitle in reel_ids:
    t += timedelta(seconds=random.randint(2, 7))
    events.append({
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "url": f"https://www.instagram.com/reels/{rid}/",
        "pageTitle": f"{rtitle} - Instagram",
        "event": "navigation"
    })

# 4. Social Comparison Session (~10 events)
t = datetime(2026, 8, 20, 15, 30, 0)
social_comp = [
    ("https://www.linkedin.com/in/rahul-sharma-sde2-google", "Rahul Sharma - Software Engineer II - Google | LinkedIn", "navigation", None),
    ("https://www.linkedin.com/in/priya-patel-senior-dev-uber", "Priya Patel - Senior Staff Engineer - Uber | LinkedIn", "navigation", None),
    ("https://www.google.com/search?q=google+l4+software+engineer+salary+bangalore+levels+fyi", "google l4 software engineer salary bangalore levels fyi - Google Search", "search_submitted", "google l4 software engineer salary bangalore levels fyi"),
    ("https://www.levels.fyi/companies/google/salaries/software-engineer/levels/l4/locations/india", "Google Software Engineer L4 Salaries in India | Levels.fyi", "navigation", None),
    ("https://www.levels.fyi/companies/uber/salaries/software-engineer/locations/india", "Uber Software Engineer Salaries in India | Levels.fyi", "navigation", None),
    ("https://www.instagram.com/travel_with_aryan/", "Aryan Mehta (@travel_with_aryan) • Instagram photos and videos - Europe Summer Trip", "navigation", None),
    ("https://www.instagram.com/fitness_vikram/", "Vikram Rao | Transformation & Lifestyle (@fitness_vikram) • Instagram", "navigation", None),
    ("https://www.google.com/search?q=how+much+salary+needed+to+be+in+top+1+percent+india+2026", "how much salary needed to be in top 1 percent india 2026 - Google Search", "search_submitted", "how much salary needed to be in top 1 percent india 2026"),
    ("https://www.linkedin.com/in/aniket-deshmukh-founder", "Aniket Deshmukh - Co-Founder & CTO @ AI Startup | LinkedIn", "navigation", None),
    ("https://www.reddit.com/r/developersIndia/comments/18x9k1l/is_it_too_late_for_25yo_to_switch_to_faang/", "Is it too late for 25yo to switch to FAANG? : r/developersIndia", "navigation", None)
]

for url, title, ev, inp in social_comp:
    t += timedelta(seconds=random.randint(45, 120))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp: e["query"] = inp
    events.append(e)

# Day 2: 2026-08-21 (Exam Study Session + Healthy Learning Philosophy)
t = datetime(2026, 8, 21, 10, 0, 0)
exam_events = [
    ("https://www.google.com/search?q=8051+microcontroller+architecture+block+diagram+explained", "8051 microcontroller architecture block diagram explained - Google Search", "search_submitted", "8051 microcontroller architecture block diagram explained"),
    ("https://www.electronicshub.org/8051-microcontroller-architecture/", "8051 Microcontroller Architecture - Complete Overview with Pin Diagram", "navigation", None),
    ("https://www.tutorialspoint.com/embedded_systems/es_8051_microcontroller.htm", "Embedded Systems - 8051 Microcontroller - Tutorialspoint", "navigation", None),
    ("https://www.google.com/search?q=8051+timer+tmod+tcon+registers+programming+examples", "8051 timer tmod tcon registers programming examples - Google Search", "search_submitted", "8051 timer tmod tcon registers programming examples"),
    ("https://www.geeksforgeeks.org/timers-in-8051-microcontroller/", "Timers in 8051 Microcontroller - GeeksforGeeks", "navigation", None),
    ("https://nptel.ac.in/courses/106/108/106108100/", "NPTEL :: Computer Science and Engineering - Microprocessors and Microcontrollers", "navigation", None),
    ("https://drive.google.com/file/d/1xYz8051LectureNotesProfGupta/view", "Unit 3 - 8051 Instruction Set & Memory Interfacing.pdf - Google Drive", "navigation", None),
    ("https://drive.google.com/file/d/1xYz8051LectureNotesProfGupta/view", "Unit 3 - 8051 Instruction Set & Memory Interfacing.pdf - Google Drive", "input", "Page 24 Timer Mode 2 auto reload"),
    ("https://www.google.com/search?q=statistical+machine+learning+maximum+likelihood+estimation+vs+map", "statistical machine learning maximum likelihood estimation vs map - Google Search", "search_submitted", "statistical machine learning maximum likelihood estimation vs map"),
    ("https://www.cs.cmu.edu/~epxing/Class/10701-20/lecture/lecture4_MLE_MAP.pdf", "Lecture 4: Maximum Likelihood and MAP Estimation - CMU School of Computer Science", "navigation", None),
    ("https://www.cs.cmu.edu/~epxing/Class/10701-20/lecture/lecture4_MLE_MAP.pdf", "Lecture 4: Maximum Likelihood and MAP Estimation - CMU School of Computer Science", "input", "Gaussian conjugate prior derivation"),
    ("https://towardsdatascience.com/mle-vs-map-understanding-the-difference-with-python-examples-123", "MLE vs MAP: A Clear Comparison with Formulas - Towards Data Science", "navigation", None),
    ("https://www.google.com/search?q=support+vector+machines+dual+formulation+lagrangian+multipliers", "support vector machines dual formulation lagrangian multipliers - Google Search", "search_submitted", "support vector machines dual formulation lagrangian multipliers"),
    ("https://see.stanford.edu/materials/aimlcs229/cs229-notes3.pdf", "CS229 Lecture notes - Support Vector Machines - Andrew Ng - Stanford University", "navigation", None),
    ("https://see.stanford.edu/materials/aimlcs229/cs229-notes3.pdf", "CS229 Lecture notes - Support Vector Machines - Andrew Ng - Stanford University", "input", "KKT dual complementarity conditions"),
    ("https://www.geeksforgeeks.org/support-vector-machine-algorithm/", "Support Vector Machine (SVM) Algorithm - GeeksforGeeks", "navigation", None),
    ("https://www.google.com/search?q=sml+previous+year+exam+questions+derivation+pca+svd", "sml previous year exam questions derivation pca svd - Google Search", "search_submitted", "sml previous year exam questions derivation pca svd"),
    ("https://drive.google.com/file/d/1SML_EndSem_Exam_2025_Solution/view", "SML_EndSem_QuestionPaper_Solutions_2025.pdf - Google Drive", "navigation", None),
    ("https://drive.google.com/file/d/1SML_EndSem_Exam_2025_Solution/view", "SML_EndSem_QuestionPaper_Solutions_2025.pdf - Google Drive", "input", "Eigenvalue decomposition of covariance matrix"),
    ("https://www.youtube.com/watch?v=FgakZw6K1QQ", "StatQuest: Principal Component Analysis (PCA), Step-by-Step - YouTube", "navigation", None)
]

for url, title, ev, inp in exam_events:
    t += timedelta(seconds=random.randint(180, 420))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp:
        if ev == "search_submitted": e["query"] = inp
        else: e["input"] = inp
    events.append(e)

# 5. Healthy Learning Session (~10 events, Krishnamurti, Osho, Nietzsche, 15-30 min dwell)
t = datetime(2026, 8, 21, 16, 0, 0)
healthy_philosophy = [
    ("https://www.google.com/search?q=j+krishnamurti+the+freedom+from+the+known+summary+quotes", "j krishnamurti the freedom from the known summary quotes - Google Search", "search_submitted", "j krishnamurti the freedom from the known summary quotes"),
    ("https://jkrishnamurti.org/content/freedom-known-chapter-1", "Freedom from the Known - Chapter 1 | J. Krishnamurti Official", "navigation", None),
    ("https://www.youtube.com/watch?v=0k5X2XfK1_Y", "J. Krishnamurti - Brockwood Park 1977 - Conversation 1: What is Observation? - YouTube", "navigation", None),
    ("https://www.youtube.com/watch?v=0k5X2XfK1_Y", "J. Krishnamurti - Brockwood Park 1977 - Conversation 1: What is Observation? - YouTube", "input", "Paused at 24:12 to take notes on observer is the observed"),
    ("https://www.google.com/search?q=nietzsche+amor+fati+concept+and+eternal+recurrence", "nietzsche amor fati concept and eternal recurrence - Google Search", "search_submitted", "nietzsche amor fati concept and eternal recurrence"),
    ("https://plato.stanford.edu/entries/nietzsche/", "Friedrich Nietzsche (Stanford Encyclopedia of Philosophy)", "navigation", None),
    ("https://plato.stanford.edu/entries/nietzsche/#EterRecu", "Friedrich Nietzsche: The Eternal Recurrence of the Same - Stanford Encyclopedia of Philosophy", "navigation", None),
    ("https://www.youtube.com/watch?v=LqKjG1o8fFE", "Academy of Ideas - Nietzsche and Amor Fati: The Love of Fate - YouTube", "navigation", None),
    ("https://www.osho.com/read/books/online-library/courage-joy-living-dangerously", "Courage: The Joy of Living Dangerously - Osho Online Library", "navigation", None),
    ("https://www.notion.so/my-workspace/Philosophy-Reading-Journal", "Personal Philosophy & Reflections Journal - Notion", "navigation", None)
]

for url, title, ev, inp in healthy_philosophy:
    t += timedelta(seconds=random.randint(300, 900))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp:
        if ev == "search_submitted": e["query"] = inp
        else: e["input"] = inp
    events.append(e)

# Day 3: 2026-08-22 (AI Project Building Session + YouTube Shorts Binge)
t = datetime(2026, 8, 22, 11, 0, 0)
ai_project = [
    ("https://www.google.com/search?q=model+context+protocol+specification+anthropic+github", "model context protocol specification anthropic github - Google Search", "search_submitted", "model context protocol specification anthropic github"),
    ("https://modelcontextprotocol.io/introduction", "Introduction to Model Context Protocol (MCP) - Official Documentation", "navigation", None),
    ("https://modelcontextprotocol.io/docs/concepts/tools", "MCP Concepts: Tools & Dynamic Discovery - Documentation", "navigation", None),
    ("https://github.com/modelcontextprotocol/python-sdk", "modelcontextprotocol/python-sdk: The official Python SDK for MCP servers and clients", "navigation", None),
    ("https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/fastmcp/server.py", "FastMCP server implementation · modelcontextprotocol/python-sdk", "navigation", None),
    ("https://www.google.com/search?q=langgraph+multi+agent+state+graph+routing+human+in+the+loop", "langgraph multi agent state graph routing human in the loop - Google Search", "search_submitted", "langgraph multi agent state graph routing human in the loop"),
    ("https://langchain-ai.github.io/langgraph/concepts/multi_agent/", "Multi-Agent Architectures - LangGraph Documentation", "navigation", None),
    ("https://langchain-ai.github.io/langgraph/how-tos/human-in-the-loop/", "How to add human-in-the-loop validation - LangGraph Documentation", "navigation", None),
    ("https://github.com/langchain-ai/langgraph/tree/main/examples/multi_agent", "langgraph/examples/multi_agent at main · langchain-ai/langgraph", "navigation", None),
    ("https://www.google.com/search?q=reciprocal+rank+fusion+algorithm+dense+sparse+vector+search", "reciprocal rank fusion algorithm dense sparse vector search - Google Search", "search_submitted", "reciprocal rank fusion algorithm dense sparse vector search"),
    ("https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking", "Hybrid search scoring (RRF) - Azure AI Search | Microsoft Learn", "navigation", None),
    ("https://qdrant.tech/articles/hybrid-search/", "Hybrid Search with Qdrant: Dense and Sparse Vectors Combined", "navigation", None),
    ("https://github.com/chroma-core/chroma", "chroma-core/chroma: The AI-native open-source embedding database", "navigation", None),
    ("https://platform.openai.com/docs/guides/structured-outputs", "Structured Outputs - OpenAI API Reference Documentation", "navigation", None),
    ("https://platform.openai.com/docs/guides/function-calling", "Function Calling with Tool Definitions - OpenAI API Reference", "navigation", None),
    ("https://www.google.com/search?q=browser+use+ai+agent+playwright+python+github", "browser use ai agent playwright python github - Google Search", "search_submitted", "browser use ai agent playwright python github"),
    ("https://github.com/browser-use/browser-use", "browser-use/browser-use: Make websites accessible for AI agents", "navigation", None),
    ("https://github.com/browser-use/browser-use/blob/main/browser_use/agent/service.py", "browser_use/agent/service.py at main · browser-use/browser-use", "navigation", None),
    ("https://github.com/rohan-dev/browserMCP/pull/18", "feat: add multi-route RRF search & MCP investigation tool · Pull Request #18", "navigation", None),
    ("https://github.com/rohan-dev/browserMCP/actions", "Actions · rohan-dev/browserMCP · 38/38 tests passing", "navigation", None)
]

for url, title, ev, inp in ai_project:
    t += timedelta(seconds=random.randint(90, 240))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp:
        if ev == "search_submitted": e["query"] = inp
        else: e["input"] = inp
    events.append(e)

# 6. YouTube Shorts Binge (~30 events, random topic hopping, low dwell)
t = datetime(2026, 8, 22, 17, 30, 0)
shorts_ids = [
    ("k3J9f01LaZ", "Shorts • Insane ping pong trick shot you wont believe"),
    ("m2N8g12MbY", "Shorts • 5 life hacks for small apartments kitchen"),
    ("p4O7h23NcX", "Shorts • When you try to sleep at 2 AM meme animation"),
    ("q5P6i34OdW", "Shorts • Gordon Ramsay reacts to raw chicken disaster"),
    ("r6Q5j45PeV", "Shorts • How fast formula 1 cars actually stop"),
    ("s7R4k56QfU", "Shorts • Indian street food massive egg cheese omelette"),
    ("t8S3l67RgT", "Shorts • Guy does 100 pushups every day for 30 days result"),
    ("u9T2m78ShS", "Shorts • What happens if you drill through the earth core"),
    ("v0U1n89TiR", "Shorts • Standup comic destroys rude heckler instantly"),
    ("w1V0o90UjQ", "Shorts • Cat steals pizza slice and escapes under couch"),
    ("x2W9p01VkP", "Shorts • World smallest functioning V8 engine running on gas"),
    ("y3X8q12WlO", "Shorts • Satisfying soap cutting and kinetic sand sounds"),
    ("z4Y7r23XmN", "Shorts • Best budget smartwatch under 2000 review"),
    ("a5Z6s34YnM", "Shorts • Coding bug fixed after 6 hours was a missing semicolon"),
    ("b6A5t45ZoL", "Shorts • How magicians do the floating card illusion trick"),
    ("c7B4u56ApK", "Shorts • High speed camera capturing balloon popping underwater"),
    ("d8C3v67BqJ", "Shorts • Gym bro spotter saves guy from dropping 140kg bench"),
    ("e9D2w78CrI", "Shorts • Crazy optical illusion that will make your walls breathe"),
    ("f0E1x89DsH", "Shorts • When teacher says test is open book but questions are impossible"),
    ("g1F0y90EtG", "Shorts • Restoring 50 year old rusty pocket knife ASMR"),
    ("h2G9z01FuF", "Shorts • How noise cancelling headphones actually block sound"),
    ("i3H8a12GvE", "Shorts • Japanese puzzle box opening sequence with secret switch"),
    ("j4I7b23HwD", "Shorts • What happens if lightning strikes an ocean"),
    ("k5J6c34IxC", "Shorts • Dog pretends to be asleep so owner doesn't give bath"),
    ("l6K5d45JyB", "Shorts • Top 3 underrated anime fights of 2026"),
    ("m7L4e56KzA", "Shorts • Real reason why airline windows have tiny pinholes"),
    ("n8M3f67Lz9", "Shorts • Smart chess trap that wins queen in 5 moves"),
    ("o9N2g78Mz8", "Shorts • Satisfying wood carving of miniature wooden house"),
    ("p0O1h89Nz7", "Shorts • How much money top YouTubers make per 1M views"),
    ("q1P0i90Oz6", "Shorts • Why doomscrolling shorts feels addictive explained")
]

for sid, stitle in shorts_ids:
    t += timedelta(seconds=random.randint(3, 9))
    events.append({
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "url": f"https://www.youtube.com/shorts/{sid}",
        "pageTitle": f"{stitle} - YouTube",
        "event": "navigation"
    })

# 7. Late Night Usage Session (~15 events, between 12AM-2AM, random browsing & weak focus)
t = datetime(2026, 8, 23, 0, 15, 0)
late_night = [
    ("https://www.google.com/search?q=why+do+i+feel+more+creative+at+night+psychology", "why do i feel more creative at night psychology - Google Search", "search_submitted", "why do i feel more creative at night psychology"),
    ("https://www.reddit.com/r/AskReddit/comments/192k8pl/night_owls_what_is_the_strangest_rabbit_hole_you/", "Night owls, what is the strangest rabbit hole you went down at 1 AM? : r/AskReddit", "navigation", None),
    ("https://en.wikipedia.org/wiki/Bimanual_coordination", "Bimanual coordination - Wikipedia", "navigation", None),
    ("https://en.wikipedia.org/wiki/Fermi_paradox", "Fermi paradox - Wikipedia", "navigation", None),
    ("https://www.google.com/search?q=great+filter+hypothesis+aliens+exist", "great filter hypothesis aliens exist - Google Search", "search_submitted", "great filter hypothesis aliens exist"),
    ("https://www.youtube.com/watch?v=UjtOGPJ0URM", "Kurzgesagt - The Great Filter: Why We Might Be Alone - YouTube", "navigation", None),
    ("https://www.google.com/search?q=best+sci+fi+books+cosmic+horror+existential+dread", "best sci fi books cosmic horror existential dread - Google Search", "search_submitted", "best sci fi books cosmic horror existential dread"),
    ("https://www.goodreads.com/book/show/20518872-the-three-body-problem", "The Three-Body Problem (Remembrance of Earth's Past, #1) by Liu Cixin | Goodreads", "navigation", None),
    ("https://www.google.com/search?q=why+is+it+hard+to+sleep+after+looking+at+screen", "why is it hard to sleep after looking at screen - Google Search", "search_submitted", "why is it hard to sleep after looking at screen"),
    ("https://www.sleepfoundation.org/bedroom-environment/blue-light", "Blue Light: What It Is and How It Affects Sleep | Sleep Foundation", "navigation", None),
    ("https://www.instagram.com/direct/inbox/", "Messages • Direct - Instagram", "navigation", None),
    ("https://www.instagram.com/reels/C9xZ99LateNight1/", "Reels • Aesthetic midnight rain vibes with lofi hip hop - Instagram", "navigation", None),
    ("https://www.instagram.com/reels/C9xZ99LateNight2/", "Reels • Relatable sleepless thoughts at 1:45 AM - Instagram", "navigation", None),
    ("https://www.google.com/search?q=sound+of+rain+for+sleeping+black+screen", "sound of rain for sleeping black screen - Google Search", "search_submitted", "sound of rain for sleeping black screen"),
    ("https://www.youtube.com/watch?v=mPZkdNFkNps", "Rain Sounds 10 Hours Black Screen - Heavy Rain & Thunder for Sleeping - YouTube", "navigation", None)
]

for url, title, ev, inp in late_night:
    t += timedelta(seconds=random.randint(60, 240))
    e = {"timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "url": url, "pageTitle": title, "event": ev}
    if inp:
        if ev == "search_submitted": e["query"] = inp
        else: e["input"] = inp
    events.append(e)

with open('scratch_events.jsonl', 'w', encoding='utf-8') as f:
    for e in events:
        f.write(json.dumps(e, ensure_ascii=False) + '\n')

print(f"Done generating {len(events)} events.")
