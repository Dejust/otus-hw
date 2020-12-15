local upperCase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
local lowerCase = "abcdefghijklmnopqrstuvwxyz"

math.randomseed(os.time())

genreateName = function ()
   local rand = math.random(#upperCase)
   local output = string.sub(upperCase, rand, rand)

   rand = math.random(#lowerCase)
   output = output .. string.sub(lowerCase, rand, rand)

   rand = math.random(#lowerCase)
   output = output .. string.sub(lowerCase, rand, rand)

   return output
end

request = function()
   local path = "/api/users/?first_name_prefix=" .. genreateName() .. "&" .. "last_name_prefix=" .. genreateName()
   return wrk.format(nil, path)
end
