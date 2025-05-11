/**
 * Backend Types
 */

export type Metadata = {
    count: number,
}

export type Collection<Type> = {
    metadata: Metadata,
    contents: Type[],
}

export type Account = {
    id: string,
    username: string,
    profile_image: string | null,
    display_name: string | null,
}

export type AuthenticatedAccount = Account & {
    email: string,
}

export type Board = {
    id: string,
    identifier: string,
    name: string,
    icon: string,
    owner_id: string,
    public: boolean,
}

export type ItemType = 'note' | 'link' | 'media' | 'todo' | 'list' | 'document'
export type Item = {
    id: string,
    board_id: string,
    position: string | null,
    list_id: string | null,
    index: number | null,
    pin: Pin | null,
    type: ItemType,
}

export type ItemNote = Item & {
    text: string,
}

export type ItemLink = Item & {
    title: string,
    url: string,
}

export type ItemImage = Item & {
    url: string,
    size: [number, number]
}

export type ItemList = Item & {
    title: string,
    items: Collection<Item> | null;
}

export type ItemTodo = Item & {
    text: string,
    items: Collection<TodoItem> | null;
}

export type ItemDocument = Item & {
    title: string,
    text: string,
}

export type TodoItem = {
    id: string,
    list_id: string,
    text: string,
    link: string | null,
    done: boolean,
}

export type Pin = {
    id: string,
    board_id: string,
    item_id: string,
    label: string | null,
    compass: boolean
    connections: string[],
}

export type MediaImage = {
    id: string,
    filename: string,
}

export type Report = {
    id: string,
    account_id: string,
    entity_id: string,
    entity_type: string,
    report_type: string,
    status: string,
    moderator_id: string | null,
    created_at: Date,
    resolved_at: Date | null,
}

/**
 * Other Types
 */

export type BadRequest = {
    error: string,
    message: string,
    detail: object | null,
}

export type CookieSettings = {
    [key: string]: {
        key: string,
        value: string,
        options: { [key: string]: string | Date | number | boolean, }
    }
};

export type CookiePromise<T = void> = Promise<[T, CookieSettings | null]>;

/**
 * Objects
 */

export const nullAccount: Account = { id: 'null', username: 'unavailable', display_name: '[Unavailable]', profile_image: null }

/**
 * Enums
 */

export enum AuthResponse {
    Success,
    InvalidCredentials,
    UsernameTaken,
    EmailTaken,
}

/**
 * Exceptions
 */

export class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, body: BadRequest) {
        super(body.message)
        this.status = status;
        this.code = body.error;
    }
}