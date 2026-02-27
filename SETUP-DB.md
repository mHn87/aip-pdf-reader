# Database setup (Supabase / PostgreSQL)

1. In `.env` add (use your Supabase connection strings):

   ```
   DATABASE_URL="postgresql://...?pgbouncer=true"
   DIRECT_URL="postgresql://...:5432/..."
   ```

2. Create tables:

   ```bash
   npx prisma db push
   ```

3. Run the app:

   ```bash
   npm run dev
   ```

4. **Batch parse test**  
   - Open **Batch parse**, paste the 3 AIP URLs (one per line), click **Validate & create job**.  
   - You are redirected to the job page; the app will parse PDFs one by one.  
   - When the job finishes with **success**, open **Parsed AIPs** (or use the link “View parsed AIPs from this job”) to see the grid.  
   - Click an AIP to open the read-only view (obstacles + runways).
