import asyncio
import asyncpg

async def create_schema():
    database_url = "postgresql://dev:devpass@localhost:5432/rag_chatbot"
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✓ Connected to database")
        
        # Drop and recreate tables with correct schema
        await conn.execute('DROP TABLE IF EXISTS "Element" CASCADE;')
        await conn.execute('DROP TABLE IF EXISTS "Step" CASCADE;')
        await conn.execute('DROP TABLE IF EXISTS "Thread" CASCADE;')
        await conn.execute('DROP TABLE IF EXISTS "User" CASCADE;')
        
        # Create tables with all required columns
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS "Thread" (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                "createdAt" TIMESTAMP DEFAULT NOW(),
                "updatedAt" TIMESTAMP DEFAULT NOW(),
                name TEXT,
                "userId" TEXT,
                metadata JSONB DEFAULT '{}'::jsonb
            );
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS "Step" (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT,
                type TEXT,
                "threadId" UUID REFERENCES "Thread"(id) ON DELETE CASCADE,
                "showInput" TEXT,
                "parentId" UUID,
                "createdAt" TIMESTAMP DEFAULT NOW(),
                "updatedAt" TIMESTAMP DEFAULT NOW(),
                "startTime" TIMESTAMP,
                "endTime" TIMESTAMP,
                input TEXT,
                output TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                tags TEXT[]
            );
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS "Element" (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                "threadId" UUID REFERENCES "Thread"(id) ON DELETE CASCADE,
                "stepId" UUID REFERENCES "Step"(id) ON DELETE CASCADE,
                name TEXT,
                type TEXT,
                url TEXT,
                "objectKey" TEXT,
                mime TEXT,
                "createdAt" TIMESTAMP DEFAULT NOW(),
                "updatedAt" TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'::jsonb
            );
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS "User" (
                id TEXT PRIMARY KEY,
                "createdAt" TIMESTAMP DEFAULT NOW(),
                "updatedAt" TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'::jsonb
            );
        ''')
        
        print("✓ Database schema created successfully with all required columns")
        await conn.close()
        
    except Exception as e:
        print(f"✗ Database schema creation failed: {e}")

if __name__ == "__main__":
    asyncio.run(create_schema())