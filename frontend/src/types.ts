/**
 * Contains TypeScript types for important objects
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
    profileImage: string,
    displayName: string,
}

export type AuthenticatedAccount = {
    id: string,
    username: string,
    email: string,
    profileImage: string,
    displayName: string,
}

export type Board = {
    id: string,
    identifier: string,
    name: string,
    icon: string,
    ownerId: string,
    public: boolean,
}

export type Item = {
    id: string,
    boardId: string,
    position: string | null,
    listId: string | null,
    index: number | null,
    pin: Pin | null,
    type: string,
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
    contents: Collection<Item> | null;
}

export type ItemTodo = Item & {
    text: string,
    contents: Collection<TodoItem> | null;
}

export type ItemDocument = Item & {
    title: string,
    text: string,
}

export type TodoItem = {
    id: string,
    listId: string,
    text: string,
    link: string | null,
    done: boolean,
}

export type Pin = {
    id: string,
    boardId: string,
    itemId: string,
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
    accountId: string,
    entityId: string,
    entityType: string,
    reportType: string,
    status: string,
    moderatorId: string | null,
    created_at: Date,
    resolved_at: Date | null,
}

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

export type BadRequest = {
    error: string,
    message: string,
    detail: object | null,
}

export class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, body: BadRequest) {
        super(body.message)
        this.status = status;
        this.code = body.error;
    }
}