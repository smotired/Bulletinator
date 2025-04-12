DELETE FROM todo_items;

DELETE FROM connection_table;
DELETE FROM pins;

DELETE FROM items_note;
DELETE FROM items_link;
DELETE FROM items_media;
DELETE FROM items_todo;
DELETE FROM items WHERE items.list_id IS NOT NULL;
DELETE FROM items_list;
DELETE FROM items;

DELETE FROM editor_table;
DELETE FROM refresh_tokens;
DELETE FROM images;
DELETE FROM boards;
DELETE FROM accounts;