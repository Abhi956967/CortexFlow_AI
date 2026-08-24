import { useEffect } from "react";
import api from "../utils/axios";
import { useDispatch } from "react-redux";
import { setUserData } from "../redux/user.slice";

function useCurrentUser() {
  const dispatch = useDispatch();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const { data } = await api.get("/api/auth/me");
        if (data) {
          dispatch(setUserData(data));
        }
      } catch (error) {
        // User not logged in yet or no cookie present
        console.log("No active user session:", error.response?.status);
      }
    };
    fetchUser();
  }, [dispatch]);
}

export default useCurrentUser;
