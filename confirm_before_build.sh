echo "Local or prod?"
select yn in "Local" "Prod"; do
    case $yn in
        Local ) make docker-build-local-image; break;;
        Prod ) make docker-build-prod-image; break;;
    esac
done