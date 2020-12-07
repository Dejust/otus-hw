(function () {
  const app = Vue.createApp({});

  app.component('register-form', {
    data() {
      return {
        profile: {
          first_name: null,
          last_name: null,
          age: null,
          city: null,
          interests: null,
          gender: null
        },

        credentials: {
          email: null,
          password: null
        }
      }
    },

    methods: {
      register: function () {
        axios.post('/api/auth/register', {
          profile: this.profile,
          credentials: this.credentials
        })
          .then(function (response) {
            setAuthToken(response.data.token);
            window.location.replace('/profile.html');
          })
          .catch(function (error) {
            alert('Check your input');
          })

      }
    },

    template: `
      <form @submit.prevent="register">
        <div class="form-group">
          <label>First name</label>
          <input type="text" v-model="profile.first_name" class="form-control">
        </div>

        <div class="form-group">
          <label>Last name</label>
          <input type="text" v-model="profile.last_name" class="form-control">
        </div>

        <div class="form-group">
          <label>Age</label>
          <input type="number" v-model.number="profile.age" class="form-control">
        </div>

        <div class="form-group">
          <label>City</label>
          <input type="text" v-model="profile.city" class="form-control">
        </div>

        <div class="form-group">
          <label>Interests</label>
          <input type="text" v-model="profile.interests" class="form-control">
        </div>


        <div class="form-group">
          <label>Gender</label>
          <select class="form-control" v-model="profile.gender">
            <option value="f">Female</option>
            <option value="m">Male</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Email address</label>
          <input type="email" v-model="credentials.email" class="form-control" placeholder="Your email address">
        </div>
        
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="credentials.password" class="form-control" placeholder="Your password">
        </div>
        
        <input type="submit" class="btn btn-primary" value="Register"/>
      </form>
  `});

  app.component('login-form', {
    data() {
      return {email: null, password: null}
    },

    methods: {
      login: function () {

        axios.post('/api/auth/login', {
          email: this.email,
          password: this.password
        })
          .then(function (response) {
            setAuthToken(response.data.token);
            window.location.replace('/profile.html');
          })
          .catch(function (error) {
            alert(error.response.data.detail);
          })

      }
    },

    template: `
      <form @submit.prevent="login">
        <div class="form-group">
          <label>Email address</label>
          <input type="email" v-model="email" class="form-control" placeholder="Your email address">
        </div>
        
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" class="form-control" placeholder="Your password">
        </div>
        
        <input type="submit" class="btn btn-primary" value="Login"/>
      </form>
    `
  });

  app.mount('#auth-app');
})();
