# Song study Cleaner

# Objective
Since song doesnt have delete functionality yet (or atleast properly), this script backdoors the database and wipes out all entities assosicate with a study, so fresh payloads can be submitted.

# Instructions
1. Ensure psql client is installed and the postgres database is accessible from your machine
2. Take the song-server that is connected to the database offline. You dont want transactions happening while you do this.
3. Make a backup of the database
4. Render the sql file via: `./clean_study.sh MY_STUDY_ID > clean_my_study_id.sql`
5. Execute that sql script on the database:  `psql -U postgres -h localhost -p PORT song < clean_my_study_id.sql`


