function setAuthToken(token) {
    localStorage.setItem('jwt_token', token);
}

function getAuthToken() {
    return localStorage.getItem('jwt_token')
}

function userLogged() {
    let token = getAuthToken();
    return token !== 'undefined' && !!token;
}

function getLoggedUserId() {
    if (!userLogged()) {
        return null;
    }

    return parseInt(JSON.parse(atob(getAuthToken().split('.')[1])).user_id);
}