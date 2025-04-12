INSERT INTO accounts VALUES (1, "john_doe", "john@example.com", "hashed_password1", NULL);
INSERT INTO accounts VALUES (2, "jane_doe", "jane@example.com", "hashed_password2", NULL);

INSERT INTO boards VALUES (1, "main_board", "default", 1, true);
INSERT INTO boards VALUES (2, "child_board", "default", 1, false);
INSERT INTO boards VALUES (3, "other_board", "default", 2, true);

INSERT INTO editor_table VALUES (1, 3);

INSERT INTO items VALUES (1, 1, null, "0,0", null, null, "note");
INSERT INTO items_note VALUES (1, "Example note", "300,200");

INSERT INTO items VALUES (2, 1, null, "0,250", null, null, "link");
INSERT INTO items_link VALUES (2, "Link to Child Board", "/boards/2");

INSERT INTO items VALUES (3, 1, null, "350,0", null, null, "list");
INSERT INTO items_list VALUES (3, "Example List");
INSERT INTO items VALUES (4, 1, 3, null, 0, null, "note");
INSERT INTO items_note VALUES (4, "List Item 1", "300,200");
INSERT INTO items VALUES (5, 1, 3, null, 1, null, "note");
INSERT INTO items_note VALUES (5, "List Item 2", "300,200");

INSERT INTO items VALUES (6, 1, null, "700,0", null, null, "todo");
INSERT INTO items_todo VALUES (6, "Todo List");
INSERT INTO todo_items VALUES (1, 6, "Plan API", null, true);
INSERT INTO todo_items VALUES (2, 6, "Read Other Board", "/boards/3", false);
INSERT INTO todo_items VALUES (3, 6, "Finish API", null, false);

INSERT INTO pins VALUES (1, "Home", true, 1, 1);
INSERT INTO pins VALUES (2, "List", false, 1, 2);
INSERT INTO pins VALUES (3, null, false, 1, 5);
INSERT INTO connection_table VALUES (1, 2);
INSERT INTO connection_table VALUES (2, 1);